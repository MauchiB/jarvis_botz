import os
from functools import wraps
from jarvis_botz.bot.db.schemas import User, Sub
from jarvis_botz.bot.db.user_repo import RedisPersistence
from typing import List, Tuple, Union, cast, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import math
from uuid import uuid4
from telegram.ext import ContextTypes
import time
from sqlalchemy import Boolean, String, Numeric, Integer
from jarvis_botz.ai.llm import AIGraph
from jarvis_botz.bot.contexttypes import CustomTypes
from langchain_core.prompts import ChatPromptTemplate

from datetime import datetime, timezone
from jarvis_botz.bot.keyboard_format import PROMPT_CONFIGURATION


from jarvis_botz.ai.prompts import get_job_system_prompt, get_name_generation_prompt



def format_user_settings(user_data: dict, config_map: dict):
    formatted_dict = {}
    
    for key, value in user_data.items():
        if key in config_map:

            display_value = config_map[key].get(value, value)
            formatted_dict[key] = display_value

        else:
            formatted_dict[key] = value
            
    return formatted_dict
        



def create_grid_paged_menu(all_items: List[Union[Tuple[str, str], InlineKeyboardButton]],
                           prefix:str,
                           action:str,
                           page: int = 0, col: int = 1, row: int = 1,
                           quit_button:str='_quit_return') -> InlineKeyboardMarkup:
    
    ITEMS_PER_PAGE = col * row

    total_items = len(all_items)
    
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    page = max(0, min(page, total_pages - 1))

    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    page_items = all_items[start_index:end_index]
    
    keyboard = []
    current_row = []
    
    for i, data in enumerate(page_items):
        if isinstance(data, InlineKeyboardButton):
            button = data
        elif isinstance(data, tuple):
            text, callback_data = data
            button = InlineKeyboardButton(text, callback_data=f"{prefix}:{action}:{callback_data}")
        
        current_row.append(button)
        

        if len(current_row) == col or i == len(page_items) - 1:
            keyboard.append(current_row)
            current_row = []

    nav_row = []
    

    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}:page:{page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(" ", callback_data="ignore")) 
        
    nav_row.append(InlineKeyboardButton(f"Page. {page + 1}/{total_pages}", callback_data="ignore"))
    

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}:page:{page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(" ", callback_data="ignore"))


    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton("❌ Выйти", callback_data=f'{prefix}:quit:{quit_button}')])

    return InlineKeyboardMarkup(keyboard)



async def initialize_new_chat_session(update: Update, context: CustomTypes, 
                     query:str, answer:str, session_id:str) -> str:

    name = await context.llm.custom_generation(prompt_func=get_name_generation_prompt, 
                                               query=query, 
                                               answer=answer)

    await context.chat_repo.update_chat_metadata(user_id=update.effective_user.id, session_key=session_id, metadata={
        'name': name,
        'session_id': session_id,
        'user_id': update.effective_user.id,
        'created_at': int(time.time()),
        'last_interaction': int(time.time()),
        'ai_settings': context.user_data.get('ai_settings', {}),
        'last_query': query,
        'last_answer': answer,
        'num_messages':1})

    return session_id


async def get_job_text(context: CustomTypes, query:str, answer:str) -> str:
    response = await context.llm.custom_generation(
                                                   prompt_func=get_job_system_prompt,
                                                   query=query, 
                                                   answer=answer
                                                   )
    
    return response
    




friendly_names = {
        'style': '🎨 Стиль',
        'temperature': '🔥 Температура',
        'system_prompt': '📝 Промпт',
        'max_tokens': '📊 Лимит токенов',
        'language': '🌐 Язык',
        'model': '🧠 Модель ИИ' # Пример на будущее
    }

def get_profile_text(user: User, ai_settings: dict) -> str:
    # 1. Блок основной информации (SQL)
    role_emoji = "👑" if user.role in ['admin', 'developer'] else "👤"
    
    text = (
        "<b>📂 ВАШ ПАСПОРТ</b>\n"
        f"<b>🆔 ID:</b> <code>{user.id}</code>\n"
        f"<b>{role_emoji} Роль:</b> <code>{user.role.upper()}</code>\n"
        f"<b>👤 Логин:</b> @{user.username or '—'}\n"
        f"<b>🪙 Баланс:</b> <code>{user.tokens:.2f} токенов</code>\n"
        f"<b>📅 В боте с:</b> <code>{user.created_at.strftime('%d.%m.%Y')}</code>\n"
    )

    # 2. Блок Реферальной системы (SQL Relationships)
    text += "\n<b>👥 РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n"
    
    # Считаем количество приглашенных через list len (если рефералы загружены)
    # Или через count в репозитории (что эффективнее для больших данных)
    ref_count = len(user.referrals)
    text += f"<b>📈 Приглашено:</b> <code>{ref_count} чел.</code>\n"
    
    # Показываем, кто пригласил (если есть)
    if user.referral:
        # Пытаемся взять юзернейм пригласителя, если он подгружен
        ref_by = f"@{user.referral.username}" if user.referral.username else f"<code>{user.referral_id}</code>"
        text += f"<b>🤝 Вас пригласил:</b> {ref_by}\n"
    elif user.referral_id:
        # Если объект referrer не подгружен (lazy load), пишем просто ID
        text += f"<b>🤝 Вас пригласил:</b> <code>{user.referral_id}</code>\n"

    # 3. Блок подписки (SQL Relationship)
    text += "\n<b>💎 СТАТУС ПОДПИСКИ</b>\n"
    
    if user.subscribers:
        # Берем последнюю подписку
        sub = user.subscribers[-1]
        now = datetime.now(timezone.utc)
        
        if sub.subscription_end_date > now:
            days_left = (sub.subscription_end_date - now).days
            text += f"<b>✅ Активна:</b> до <code>{sub.subscription_end_date.strftime('%d.%m.%Y')}</code>\n"
            text += f"<b>⏳ Осталось:</b> <code>{days_left} дн.</code>\n"
        else:
            text += "<i>❌ Подписка истекла</i>\n"
    else:
        text += "<i>🆓 Бесплатный тариф</i>\n"

    # 4. Блок настроек ИИ (Redis)
    text += "\n<b>🤖 НАСТРОЙКИ ИНТЕЛЛЕКТА</b>\n"
    
    if not ai_settings:
        text += "<i>⚙️ Настройки еще не заданы</i>\n"
    else:
        for key, value in ai_settings.items():
            name = friendly_names.get(key, f"⚙️ {key.capitalize()}")
            display_value = str(value)
            if len(display_value) > 30:
                display_value = display_value[:27] + "..."
            text += f"<b>{name}:</b> <code>{display_value}</code>\n"

    return text


def check_user(need_chat=False, ban_check=True, add_ref=False):
    def decorator(func):

        @wraps(func)
        async def wrapper(update: Update, context: CustomTypes):
            async with context.session_factory() as session:
                rep = context.user_repo(session=session)
                user = await rep.get_user(update.effective_user.id)
                
                if not user:
                    user = await rep.add_user(id=update.effective_user.id, 
                                       username=update.effective_user.username, 
                                       chat_id=update.effective_chat.id)
                    

                    context.user_data['ai_settings'] = {}
                    if add_ref:
                        if context.args:
                            try:
                                ref_user_id = int(context.args[0])
                            except:
                                print(f'ID {ref_user_id} is {type(ref_user_id)}')

                            await rep.update_ref_user(user_id=user.id, ref_user_id=ref_user_id)
                                
                        await session.commit()
                    
                if ban_check and user:
                    if user.is_banned:
                        await update.effective_message.reply_text('Ваш аккаунт заблокирован. Пока!')
                        return
                
                if need_chat:
                    if not context.user_data.get('session_id', None):
                        await update.effective_message.reply_text('У вас нет активного чата. Пожалуйста, выберите или создайте чат перед отправкой сообщений.')
                        return

                    
            
            return await func(update, context)
        
        return wrapper
    
    return decorator


def control_tokens(required_tokens: float):
    def decorator(func):

        @wraps(func)
        async def wrapper(update, context: CustomTypes):
            async with context.session_factory() as session:
                rep = context.user_repo(session=session)
                user = await rep.get_user(update.effective_user.id)
                if user.tokens < required_tokens:
                    await update.effective_message.reply_text('У вас недостаточно токенов для выполнения этого действия. Пожалуйста, пополните свой баланс токенов.')
                    return
                token_after = user.tokens - required_tokens
                await rep._set_attr(id=update.effective_user.id, update_data={'tokens':token_after})

                return await func(update, context)
        
        return wrapper
    
    return decorator




def required_permission(roles, need_alert=True):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context: CustomTypes):
            async with context.session_factory() as session:
                rep = context.user_repo(session=session)
                user = await rep.get_user(update.effective_user.id)
                if user.role in roles:
                    return await func(update, context)
                
                if need_alert:
                    await update.effective_message.reply_text('У вас нет доступа к этой команде.')
                return
            
        return wrapper

    return decorator







async def set_type(column_name: str, input_value: str):
    try:
        column = getattr(User, column_name)
    except AttributeError:
        raise ValueError(f"Column: {column_name} don`t found")
        
    column_type = column.type
    lower_value = input_value.lower()


    if isinstance(column_type, Boolean):
        lower_value = input_value.lower()
        if lower_value in ['true', '1']:
            return True
        elif lower_value in ['false', '0']:
            return False
        else:
            raise ValueError(f"{input_value} - need to be bool object (true or 1 / false or 0)")

    elif isinstance(column_type, Integer):
        try:
            return int(input_value)
        except ValueError:
            raise ValueError(f"{input_value} - need to be int object (any number)")


    elif isinstance(column_type, Numeric):
        try:
            return float(input_value)
        except ValueError:
            raise ValueError(f"{input_value} - need to be numeric object like (float)")


    elif isinstance(column_type, String):
        try:
            return str(input_value)
        except ValueError:
            raise ValueError(f"{input_value} - need to be str object (any text)")
    