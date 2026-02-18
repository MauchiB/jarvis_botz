from __future__ import annotations

from typing import Optional
from telegram import Update, CallbackQuery

from jarvis_botz.utils import (
    check_user,
    get_profile_text,
    create_grid_paged_menu,
)
from jarvis_botz.bot.keyboards import (
    start_keyboard,
    settings_keyboard_markup,
    data_items,
    help_text,
)
from jarvis_botz.bot.contexttypes import CustomTypes



TEXT_START = (
    "Привет! Я Jarvis ваш персональный AI-ассистент.\n"
    "Как я могу служить вам сегодня? (/help для подробной информации)"
)

TEXT_SETTINGS_MENU = "Выбор настроек для ИИ:"
ACTION_SELECT = "select"
ACTION_QUIT = "quit"
QUIT_DELETE = "_quit_delete"
QUIT_RETURN = "_quit_return"



@check_user(add_ref=True)
async def start(update: Update, context: CustomTypes) -> None:
    await update.effective_message.reply_text(
        TEXT_START,
        reply_markup=start_keyboard,
    )



async def help_handler(update: Update, context: CustomTypes) -> None:
    await update.effective_message.reply_text(
        help_text,
        parse_mode="HTML",
    )



@check_user()
async def ai_settings_menu_handler(update: Update, context: CustomTypes) -> None:
    callback: Optional[CallbackQuery] = update.callback_query

    if callback:
        await callback.answer()
        await update.effective_message.edit_text(
            TEXT_SETTINGS_MENU,
            reply_markup=settings_keyboard_markup,
        )
        return

    await update.effective_message.reply_text(
        TEXT_SETTINGS_MENU,
        reply_markup=settings_keyboard_markup,
    )



@check_user()
async def choose_setting_menu_callback(
    update: Update,
    context: CustomTypes,
) -> None:

    callback: CallbackQuery = update.callback_query
    if not callback or not callback.data:
        return

    await callback.answer()

    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    prefix, _, page_raw = parts
    page: int = int(page_raw) if page_raw.isdigit() else 0

    items = data_items.get(prefix, [])
    keyboard = create_grid_paged_menu(
        all_items=items,
        prefix=prefix,
        action=ACTION_SELECT,
        page=page,
        col=1,
        row=5,
        quit_button=QUIT_DELETE,
    )

    await update.effective_message.edit_text(
        f"Выберите {prefix} для бота:",
        reply_markup=keyboard,
    )



@check_user()
async def apply_setting_choice_callback(
    update: Update,
    context: CustomTypes,
) -> None:

    callback: CallbackQuery = update.callback_query
    if not callback or not callback.data:
        return

    await callback.answer()

    parts = callback.data.split(":")
    if len(parts) < 3:
        return

    prefix, action, value = parts


    ai_settings = context.user_data.setdefault("ai_settings", {})

    if action == ACTION_SELECT:
        ai_settings[prefix] = value
        await ai_settings_menu_handler(update, context)
        return

    if action == ACTION_QUIT and value == QUIT_DELETE:
        await callback.delete_message()
        return

    if action == ACTION_QUIT and value == QUIT_RETURN:
        await ai_settings_menu_handler(update, context)



@check_user()
async def reset_settings_callback(
    update: Update,
    context: CustomTypes,
) -> None:

    callback: CallbackQuery = update.callback_query
    if callback:
        await callback.answer("Настройки сброшены", show_alert=True)

    context.user_data["ai_settings"] = {}



@check_user()
async def user_info_handler(update: Update, context: CustomTypes) -> None:
    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)
        user = await user_repo.get_user(id=update.effective_user.id)

        if not user:
            await update.effective_message.reply_text("User isn`t defined")
            return

        ai_settings = context.user_data.get("ai_settings", {})
        text = get_profile_text(user, ai_settings=ai_settings)

        await update.effective_message.reply_text(text, parse_mode="HTML")


