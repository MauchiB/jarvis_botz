from __future__ import annotations

import json
import uuid
import logging
from typing import Any, Dict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Poll,
    helpers,
)

from jarvis_botz.bot.contexttypes import CustomTypes
from jarvis_botz.utils import get_job_text
from jarvis_botz.ai.prompts import get_inline_fast_help_prompt


logger = logging.getLogger(__name__)



TEMP_GRADE_KEY = "temporary_answer_grade"
GLOBAL_GRADE_KEY = "global_answer_grade"

POLL_CHOICES = [
    "⭐️ Ужасно",
    "⭐️⭐️ Плохо",
    "⭐️⭐️⭐️ Ок",
    "⭐️⭐️⭐️⭐️ Хорошо",
    "⭐️⭐️⭐️⭐️⭐️ Супер",
]




async def query_handler(update: Update, context: CustomTypes) -> None:
    inline_query = update.inline_query
    if not inline_query or not inline_query.query:
        return

    query = inline_query.query.strip()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Обработка запроса...", callback_data="none")]
    ])

    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title="Спроси Jarvis Botz",
        description=f"Jarvis ответит на: {query}",
        input_message_content=InputTextMessageContent(
            message_text=f"<b>Вопрос: {query}</b>\nJarvis Botz: думаю...",
            parse_mode="HTML",
        ),
        reply_markup=keyboard,
    )

    await inline_query.answer(results=[result], cache_time=60)




async def chosen_query_handler(update: Update, context: CustomTypes) -> None:
    chosen = update.chosen_inline_result
    if not chosen:
        return

    query = chosen.query

    answer = await context.llm.custom_generation(
        prompt_func=get_inline_fast_help_prompt,
        query=query,
    )

    text_html = f"<b>Вопрос: {query}</b>\nJarvis Botz: {answer}"
    text_plain = f"Вопрос: {query}\nJarvis Botz: {answer}\n\nСорри, форматирование сломалось."

    try:
        await context.bot.edit_message_text(
            inline_message_id=chosen.inline_message_id,
            text=text_html,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("HTML format failed: %s", e)
        await context.bot.edit_message_text(
            inline_message_id=chosen.inline_message_id,
            text=text_plain,
        )




async def webapp_data_handler(update: Update, context: CustomTypes) -> None:
    data_raw = update.effective_message.web_app_data.data
    try:
        data = json.loads(data_raw)
    except json.JSONDecodeError:
        logger.error("Invalid webapp json")
        return

    context.user_data["session_id"] = data.get("session_id")
    context.user_data["creating_chat"] = False



async def grade_poll_handler(update: Update, context: CustomTypes, ai_answer: str) -> None:
    chat_id = update.effective_chat.id

    poll_msg = await context.bot.send_poll(
        chat_id=chat_id,
        question="Оцените качество ответа",
        options=POLL_CHOICES,
        is_anonymous=False,
        type=Poll.REGULAR,
    )

    temp_store: Dict[str, Any] = context.bot_data.setdefault(TEMP_GRADE_KEY, {})

    temp_store[poll_msg.poll.id] = {
        "user_id": chat_id,
        "answer": ai_answer,
        "chat_id": chat_id,
        "message_id": poll_msg.message_id,
    }


async def poll_answer_handler(update: Update, context: CustomTypes) -> None:
    poll_answer = update.poll_answer
    temp_store: Dict[str, Any] = context.bot_data.get(TEMP_GRADE_KEY, {})

    poll_data = temp_store.pop(poll_answer.poll_id, None)
    if not poll_data:
        return

    option = poll_answer.option_ids[0] + 1
    poll_data["option"] = option

    global_store: Dict[str, Any] = context.bot_data.setdefault(GLOBAL_GRADE_KEY, {})
    global_store[poll_answer.poll_id] = poll_data

    await context.bot.delete_message(
        chat_id=poll_data["chat_id"],
        message_id=poll_data["message_id"],
    )




async def create_deeplink(update: Update, context: CustomTypes) -> None:
    link = helpers.create_deep_linked_url(
        context.bot.username,
        payload=str(update.effective_user.id),
    )
    await update.effective_message.reply_text(f"Реферальная ссылка: {link}")




async def job_callback(context: CustomTypes) -> None:
    chat_id = context.job.chat_id

    chats = await context.chat_repo.get_all_chats(
        user_id=context.job.user_id,
        sort_key="last_interaction",
        reverse=True,
    )

    last_chat = chats[0] if chats else None
    if not last_chat:
        return

    metadata = last_chat[1]
    query = metadata.get("last_query", "Нет данных")
    answer = metadata.get("last_answer", "Нет данных")

    text = await get_job_text(context=context, query=query, answer=answer)

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


async def reschedule_inactive_message_job(update: Update, context: CustomTypes, delay: int) -> None:
    chat_id = str(update.effective_chat.id)

    for job in context.job_queue.get_jobs_by_name(chat_id):
        job.schedule_removal()

    context.job_queue.run_once(
        callback=job_callback,
        when=delay,
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id,
        name=chat_id,
    )
