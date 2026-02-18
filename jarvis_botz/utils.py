from collections.abc import Mapping
import logging
from functools import wraps
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import math
import time
from sqlalchemy import Boolean, String, Numeric, Integer
from traitlets import Any
from jarvis_botz.bot.contexttypes import CustomTypes
import json
from jarvis_botz.ai.prompts import get_job_system_prompt, get_name_generation_prompt
from typing import Dict, Union, List, Tuple
from jarvis_botz.bot.db.schemas import User


def format_user_settings(
    user_data: Mapping[str, Any],
    config_map: Mapping[str, Mapping[Any, Any]],
) -> Dict[str, Any]:
    formatted: Dict[str, Any] = {}

    for key, value in user_data.items():
        mapping = config_map.get(key)
        if mapping:
            formatted[key] = mapping.get(value, value)
        else:
            formatted[key] = value

    return formatted


IGNORE_CALLBACK = "ignore"

def create_grid_paged_menu(
    all_items: List[Union[Tuple[str, str], InlineKeyboardButton]],
    prefix: str,
    action: str,
    page: int = 0,
    col: int = 1,
    row: int = 1,
    quit_button: str = "_quit_return",
) -> InlineKeyboardMarkup:

    col = max(1, col)
    row = max(1, row)

    items_per_page = col * row
    total_items = len(all_items)
    total_pages = max(1, math.ceil(total_items / items_per_page))

    page = max(0, min(page, total_pages - 1))

    start = page * items_per_page
    end = start + items_per_page
    page_items = all_items[start:end]

    keyboard: List[List[InlineKeyboardButton]] = []
    current_row: List[InlineKeyboardButton] = []

    for i, data in enumerate(page_items):
        if isinstance(data, InlineKeyboardButton):
            button = data
        else:
            text, cb = data
            button = InlineKeyboardButton(
                text,
                callback_data=f"{prefix}:{action}:{cb}"
            )

        current_row.append(button)

        if len(current_row) == col or i == len(page_items) - 1:
            keyboard.append(current_row)
            current_row = []

    # NAVIGATION
    nav_row: List[InlineKeyboardButton] = []

    if page > 0:
        nav_row.append(
            InlineKeyboardButton("⬅️", callback_data=f"{prefix}:page:{page-1}")
        )
    else:
        nav_row.append(
            InlineKeyboardButton(" ", callback_data=IGNORE_CALLBACK)
        )

    nav_row.append(
        InlineKeyboardButton(
            f"{page+1}/{total_pages}",
            callback_data=IGNORE_CALLBACK
        )
    )

    if page < total_pages - 1:
        nav_row.append(
            InlineKeyboardButton("➡️", callback_data=f"{prefix}:page:{page+1}")
        )
    else:
        nav_row.append(
            InlineKeyboardButton(" ", callback_data=IGNORE_CALLBACK)
        )

    keyboard.append(nav_row)

    # QUIT
    keyboard.append([
        InlineKeyboardButton("❌ Выйти", callback_data=f"{prefix}:quit:{quit_button}")
    ])

    return InlineKeyboardMarkup(keyboard)




logger = logging.getLogger(__name__)

async def initialize_new_chat_session(
    update: Update,
    context: CustomTypes,
    query: str,
    answer: str,
    session_id: str,
) -> str:

    chat_repo = context.chat_repo
    user_id = update.effective_user.id
    now = int(time.time())

    # NAME GENERATION
    try:
        name = await context.llm.custom_generation(
            prompt_func=get_name_generation_prompt,
            query=query,
            answer=answer,
        )
    except Exception as e:
        logger.warning("Name generation failed, fallback used", exc_info=e)
        name = "Новый чат"

    await chat_repo.add_chat_session(
        user_id=user_id,
        session_id=session_id,
    )

    metadata = {
        "name": name,
        "session_id": session_id,
        "user_id": user_id,
        "created_at": now,
        "last_interaction": now,
        "ai_settings": json.dumps(context.user_data.get("ai_settings", {})),
        "last_query": query,
        "last_answer": answer,
        "num_messages": 1,
    }

    await chat_repo.update_chat_metadata(
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
    )

    return session_id




async def get_job_text(
    context: CustomTypes,
    query: str,
    answer: str,
) -> str:

    try:
        response = await context.llm.custom_generation(
            prompt_func=get_job_system_prompt,
            query=query,
            answer=answer,
        )

        return response or "Возвращайтесь в чат 😉"

    except Exception as e:
        logger.error("Job text generation failed", exc_info=e)
        return "Мы скучаем по вам! Возвращайтесь в чат 🤖"





friendly_names = {
        'style': '🎨 Стиль',
        'temperature': '🔥 Температура',
        'system_prompt': '📝 Промпт',
        'max_tokens': '📊 Лимит токенов',
        'language': '🌐 Язык',
        'model': '🧠 Модель ИИ' # Пример на будущее
    }


def get_profile_text(user: User, ai_settings: dict) -> str:
    role_emoji: str = "👑" if user.role in {"admin", "developer"} else "👤"
    username: str = user.username or "—"

    text: str = (
        "<b>📂 ВАШ ПАСПОРТ</b>\n"
        f"<b>🆔 ID:</b> <code>{user.id}</code>\n"
        f"<b>{role_emoji} Роль:</b> <code>{user.role.upper()}</code>\n"
        f"<b>👤 Логин:</b> @{username}\n"
        f"<b>🪙 Баланс:</b> <code>{user.tokens:.2f} токенов</code>\n"
        f"<b>📅 В боте с:</b> <code>{user.created_at:%d.%m.%Y}</code>\n"
    )

    # --- Рефералы ---
    text += "\n<b>👥 РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n"

    ref_count: int = len(user.referrals or [])
    text += f"<b>📈 Приглашено:</b> <code>{ref_count} чел.</code>\n"

    if user.referral:
        ref_by: str = (
            f"@{user.referral.username}"
            if user.referral.username
            else f"<code>{user.referral_id}</code>"
        )
        text += f"<b>🤝 Вас пригласил:</b> {ref_by}\n"
    elif user.referral_id:
        text += f"<b>🤝 Вас пригласил:</b> <code>{user.referral_id}</code>\n"


    # --- AI настройки ---
    text += "\n<b>🤖 НАСТРОЙКИ ИНТЕЛЛЕКТА</b>\n"

    if not ai_settings:
        text += "<i>⚙️ Настройки еще не заданы</i>\n"
    else:
        for key, value in ai_settings.items():
            name: str = friendly_names.get(key, f"⚙️ {key.capitalize()}")
            display_value: str = str(value)

            if len(display_value) > 30:
                display_value = f"{display_value[:27]}..."

            text += f"<b>{name}:</b> <code>{display_value}</code>\n"

    return text



def check_user(need_chat: bool = False, ban_check: bool = True, add_ref: bool = False):
    def decorator(func):

        @wraps(func)
        async def wrapper(update: Update, context: CustomTypes):

            async with context.session_factory() as session:
                repo = context.user_repo(session=session)
                user_id = update.effective_user.id
                username = update.effective_user.username
                chat_id = update.effective_chat.id

                user = await repo.get_user(user_id)


                if not user:
                    user = await repo.add_user(
                        id=user_id,
                        username=username,
                        chat_id=chat_id
                    )

                    context.user_data.setdefault("ai_settings", {})

                    if add_ref:
                        ref_user_id = None
                        args = getattr(context, "args", None)

                        if args:
                            try:
                                ref_user_id = int(args[0])
                            except ValueError:
                                ref_user_id = None

                        if ref_user_id:
                            await repo.update_ref_user(
                                user_id=user.id,
                                ref_user_id=ref_user_id
                            )

                    await session.commit()


                if ban_check and user.is_banned:
                    await update.effective_message.reply_text(
                        "Ваш аккаунт заблокирован."
                    )
                    return


                if need_chat and not context.user_data.get("session_id"):
                    await update.effective_message.reply_text(
                        "Нет активного чата. Создайте или выберите чат."
                    )
                    return

            return await func(update, context)

        return wrapper

    return decorator



async def control_tokens(
    update: Update,
    context: CustomTypes,
    text_tokens: float = 0,
    image_tokens: float = 0,
    document_tokens: float = 0
) -> Tuple[bool, float, float]:

    message = update.effective_message


    required_tokens = 0.0

    if message.photo:
        required_tokens += image_tokens

    if message.text or message.caption:
        required_tokens += text_tokens

    if message.document:
        required_tokens += document_tokens

    required_tokens = max(0, round(required_tokens, 2))

    async with context.session_factory() as session:
        repo = context.user_repo(session=session)
        user_id = update.effective_user.id
        user = await repo.get_user(user_id)

        if not user:
            return False, 0, required_tokens

        if user.tokens < required_tokens:
            return False, user.tokens, required_tokens


        new_balance = max(0, round(user.tokens - required_tokens, 2))

        await repo._set_attr(
            id=user_id, 
            update_data={'tokens': new_balance}
        )

        return True, new_balance, required_tokens







def required_permission(roles, need_alert: bool = True):
    roles = set(roles) if isinstance(roles, (list, tuple, set)) else {roles}

    def decorator(func):

        @wraps(func)
        async def wrapper(update: Update, context: CustomTypes):

            async with context.session_factory() as session:
                repo = context.user_repo(session=session)
                user = await repo.get_user(update.effective_user.id)

                if not user:
                    await update.effective_message.reply_text("Пользователь не найден.")
                    return

                if user.role not in roles:
                    if need_alert:
                        await update.effective_message.reply_text(
                            "У вас нет доступа к этой команде."
                        )
                    return

            return await func(update, context)

        return wrapper

    return decorator







def set_type(column_name: str, input_value: str):

    try:
        column_attr = getattr(User, column_name)
        column = column_attr.property.columns[0]
    except AttributeError:
        raise ValueError(f"Column '{column_name}' not found")

    column_type = column.type

    if input_value is None:
        return None

    value = input_value.strip()

    # --- BOOLEAN ---
    if isinstance(column_type, Boolean):
        v = value.lower()
        if v in {"true", "1", "yes", "y", "on"}:
            return True
        if v in {"false", "0", "no", "n", "off"}:
            return False
        raise ValueError(f"{input_value} must be boolean")


    if isinstance(column_type, Integer):
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"{input_value} must be integer")

 
    if isinstance(column_type, Numeric):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            raise ValueError(f"{input_value} must be numeric")


    if isinstance(column_type, String):
        return value


    return value

        
        
