from jarvis_botz.bot.database import get_user
from jarvis_botz.config import config
import os
from functools import wraps
from jarvis_botz.bot.database import User, get_user, add_user, _set_attr, get_chat_redis, create_chat_redis
from typing import List, Tuple, Union
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import math
from uuid import uuid4
from telegram.ext import ContextTypes
import time

from jarvis_botz.ai.graph import graph


from langchain_core.prompts import ChatPromptTemplate

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



async def initialize_new_chat_session(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                     question:str, answer:str, session_id:str) -> str:
    
    name = await graph.name_generation(question=question, answer=answer)

    await create_chat_redis(prefix_metadata='user_chat_metadata', name=update.effective_user.id, key=session_id, metadata={
        'name': name,
        'session_id': session_id,
        'user_id': update.effective_user.id,
        'created_at': int(time.time())})

    return session_id
    






def get_attr_table(user: User) -> str:
    info = ''
    
    for column in user.__table__.columns:
        value = getattr(user, column.name)
        info += f'{column.name} - {value} \n'


    return info




def check_user(need_chat=False, ban_check=True):
    def decorator(func):

        @wraps(func)
        async def wrapper(update, context):
            user = await get_user(update.effective_user.id)
            if not user:
                user = await add_user(update.effective_user.id, update.effective_user.username)
            
            if ban_check:
                if user.is_banned:
                    await update.effective_message.reply_text('Ваш аккаунт заблокирован. Пожалуйста, свяжитесь с администратором для получения дополнительной информации.')
                    return
            
            if need_chat:
                if not context.user_data.get('current_chat_id', None):
                    await update.effective_message.reply_text('У вас нет активного чата. Пожалуйста, выберите или создайте чат перед отправкой сообщений.')
                    return
            
            
            return await func(update, context)
        
        return wrapper
    
    return decorator


def control_tokens(required_tokens: float):
    def decorator(func):

        @wraps(func)
        async def wrapper(update, context):
            user = await get_user(update.effective_user.id)
            if user.tokens < required_tokens:
                await update.effective_message.reply_text('У вас недостаточно токенов для выполнения этого действия. Пожалуйста, пополните свой баланс токенов.')
                return
            
            await _set_attr(id=update.effective_user.id, column='tokens', value=user.tokens - required_tokens)

            return await func(update, context)
        
        return wrapper
    
    return decorator




def required_permission(roles, need_alert=True):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context):
            user = await get_user(update.effective_user.id)
            if user.role in roles:
                return await func(update, context)
            
            if need_alert:
                await update.effective_message.reply_text('У вас нет доступа к этой команде.')
            return
            
        return wrapper

    return decorator