from __future__ import annotations

from uuid import uuid4
from typing import List, Tuple, Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)

from jarvis_botz.utils import create_grid_paged_menu, check_user
from jarvis_botz.bot.contexttypes import CustomTypes


STATE_CHAT_NAME = 5

# ---- CALLBACK ACTIONS ----
CHAT_PREFIX = "chat"
ACTION_SELECT_FINAL = "select_final"
ACTION_DELETE_FINAL = "delete_final"
ACTION_SELECT_ACTION = "select_action"
ACTION_QUIT = "quit"

QUIT_RETURN = "_quit_return"
QUIT_DELETE = "_quit_delete"

DEFAULT_ALLOWED_CHATS = 10




def chat_create_button_action(session_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🗑️ Удалить чат",
                callback_data=f"{CHAT_PREFIX}:{ACTION_DELETE_FINAL}:{session_id}",
            ),
            InlineKeyboardButton(
                "✅ Выбрать Чат",
                callback_data=f"{CHAT_PREFIX}:{ACTION_SELECT_FINAL}:{session_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Назад",
                callback_data=f"{CHAT_PREFIX}:{ACTION_QUIT}:{QUIT_RETURN}",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)




@check_user()
async def create_chat(update: Update, context: CustomTypes) -> None:
    user_data = context.user_data

    user_data.setdefault("num_chats", 0)
    user_data.setdefault("allowed_num_chats", DEFAULT_ALLOWED_CHATS)

    num_chats: int = user_data["num_chats"]
    allowed: int = user_data["allowed_num_chats"]

    if num_chats >= allowed:
        text = (
            f"Вы не можете создать больше чем {allowed} чатов.\n"
            "Пожалуйста, удалите некоторые чаты и попробуйте снова.\n"
            "Вы остались в том же чате."
        )
        await update.effective_message.reply_text(text)
        return

    user_data["session_id"] = str(uuid4())
    user_data["creating_chat"] = True

    await update.effective_message.reply_text(
        "Чат будет создан при первом вашем сообщении в этом чате."
    )




@check_user()
async def chat_list(update: Update, context: CustomTypes) -> None:
    callback: Optional[CallbackQuery] = update.callback_query
    page: int = 0

    if callback and callback.data:
        parts = callback.data.split(":")
        if len(parts) >= 3 and parts[2].isdigit():
            page = int(parts[2])

    chat_repo = context.chat_repo
    user_id = update.effective_user.id

    chat_data: List[Tuple[str, dict]] = await chat_repo.get_all_chats(
        user_id=user_id
    )

    if not chat_data:
        text = "У вас еще нет созданных чатов. Пожалуйста, создайте чат сначала."

        if callback:
            await callback.answer()
            await update.effective_message.edit_text(text)
        else:
            await update.effective_message.reply_text(text)
        return

    buttons_data = [
        (metadata.get("name", "Без названия"), session_id)
        for session_id, metadata in chat_data
    ]

    chat_menu = create_grid_paged_menu(
        all_items=buttons_data,
        prefix=CHAT_PREFIX,
        action=ACTION_SELECT_ACTION,
        page=page,
        col=1,
        row=5,
        quit_button=QUIT_DELETE,
    )

    text = f"Управление вашими чатами ({context.user_data.get('num_chats', 0)}):"

    if callback:
        await callback.answer()
        await update.effective_message.edit_text(text, reply_markup=chat_menu)
    else:
        await update.effective_message.reply_text(text, reply_markup=chat_menu)




@check_user()
async def chat_select(update: Update, context: CustomTypes) -> None:
    callback: CallbackQuery = update.callback_query
    if not callback or not callback.data:
        return

    _, action, value = callback.data.split(":")

    chat_repo = context.chat_repo
    user_data = context.user_data
    user_id = update.effective_user.id

    
    if action == ACTION_SELECT_FINAL:
        user_data["session_id"] = value
        user_data["creating_chat"] = False
        await update.effective_message.delete()


    elif action == ACTION_DELETE_FINAL:
        if user_data.get("session_id") == value:
            user_data["session_id"] = None

        await chat_repo.delete_chat_metadata(user_id=user_id, session_id=value)
        await chat_repo.remove_chat_session(user_id=user_id, session_id=value)
        await context.llm.checkpointer.adelete_thread(thread_id=value)

        user_data["num_chats"] = max(user_data.get("num_chats", 1) - 1, 0)

        await chat_list(update, context)


    elif action == ACTION_QUIT and value == QUIT_RETURN:
        await chat_list(update, context)


    elif action == ACTION_QUIT and value == QUIT_DELETE:
        await update.effective_message.delete()


    elif action == ACTION_SELECT_ACTION:
        keyboard = chat_create_button_action(session_id=value)
        await update.effective_message.edit_text(
            "Выберите действие: удалить или выбрать чат.",
            reply_markup=keyboard,
        )

    await callback.answer()





