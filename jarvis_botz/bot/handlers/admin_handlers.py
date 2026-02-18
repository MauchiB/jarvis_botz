from __future__ import annotations

import os
import logging
import traceback
from typing import List, Optional

from telegram import Update
from telegram.ext import ContextTypes

from jarvis_botz.bot.db.user_repo import UserRepository, User
from jarvis_botz.bot.contexttypes import CustomTypes
from jarvis_botz.utils import required_permission, check_user, set_type

logger = logging.getLogger(__name__)

# ---- Константы ----
ROLE_ADMIN = "admin"
ROLE_DEVELOPER = "developer"

ACTION_SET = "set"
ACTION_GET = "get"


# ---------------- DEV COLUMN ----------------
@check_user()
@required_permission([ROLE_DEVELOPER], need_alert=True)
async def dev_column(update: Update, context: CustomTypes) -> None:
    columns: List[str] = [
        f"*{column.name}*: {column.type}"
        for column in User.__table__.columns
    ]

    text = "**All columns of database**:\n" + "\n".join(columns)
    await update.effective_message.reply_text(text, parse_mode="Markdown")


# ---------------- DEV COMMAND ----------------
@check_user()
@required_permission([ROLE_DEVELOPER], need_alert=True)
async def dev_command(update: Update, context: CustomTypes) -> None:
    args = context.args or []

    if not (3 <= len(args) <= 4):
        await update.effective_message.reply_text(
            "Need 3–4 arguments: <username> <set|get> <column> [value]"
        )
        return

    username: str = args[0]
    action: str = args[1].lower()
    column: str = args[2]

    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)
        user: Optional[User] = await user_repo.get_user(username=username)

        if not user:
            await update.effective_message.reply_text("User not found")
            return

        try:
            if action == ACTION_SET:
                if len(args) < 4:
                    await update.effective_message.reply_text("Value required")
                    return

                raw_value = args[3]
                value = await set_type(column, raw_value)

                update_data = {column: value}
                await user_repo._set_attr(
                    username=username,
                    update_data=update_data,
                )

                await update.effective_message.reply_text(
                    f"{username}: {column}={value}"
                )
                return

            if action == ACTION_GET:
                attr = getattr(user, column, None)
                if attr is None:
                    await update.effective_message.reply_text(
                        "Attribute was not found"
                    )
                else:
                    await update.effective_message.reply_text(f"Attr - {attr}")
                return

            await update.effective_message.reply_text(
                "Action must be 'set' or 'get'"
            )

        except Exception:
            logger.exception("Developer command failed")
            await update.effective_message.reply_text("Something went wrong")




async def error_handler(update: object, context: CustomTypes) -> None:
    logger.exception("Unhandled error", exc_info=context.error)

    tb_list = traceback.format_exception(
        None,
        context.error,
        context.error.__traceback__,
    )
    tb_string = "".join(tb_list)[-1000:]  # обрезаем

    try:
        async with context.session_factory() as session:
            repo = UserRepository(session=session)
            users = await repo.get_users_by_role(role=ROLE_DEVELOPER)

            for user in users or []:
                if user.chat_id:
                    await context.bot.send_message(user.chat_id, tb_string)

    except Exception:
        logger.exception("Failed to notify developers about error")



@check_user()
@required_permission([ROLE_DEVELOPER], need_alert=True)
async def error_test_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    raise ValueError("error test")




@check_user()
async def promo(update: Update, context: CustomTypes) -> None:
    admin_promo = os.getenv("ADMIN_PROMO")
    dev_promo = os.getenv("DEV_PROMO")

    if not context.args:
        return

    code = context.args[0]

    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)

        if code == admin_promo:
            await user_repo._set_attr(
                id=update.effective_user.id,
                update_data={"role": ROLE_ADMIN},
            )

        elif code == dev_promo:
            await user_repo._set_attr(
                id=update.effective_user.id,
                update_data={"role": ROLE_DEVELOPER},
            )

        else:
            await update.effective_message.reply_text("Invalid promo code")
