from telegram import Update, helpers, Poll
from jarvis_botz.bot.contexttypes import CustomTypes
from functools import wraps

from jarvis_botz.utils import get_job_text
import hashlib
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from jarvis_botz.bot.handlers.chat_handlers import chat_select
import json

from telegram.helpers import escape_markdown
from telegram.ext import InlineQueryHandler
from telegram import InlineQueryResult, InlineQueryResultArticle, InputMessageContent, InputTextMessageContent
import uuid
from jarvis_botz.ai.prompts import get_inline_fast_help_prompt


async def query_handler(update: Update, context: CustomTypes):
    query = update.inline_query.query

    if not query:
        return
    

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Обработка запроса...", callback_data="none")]
    ])
    

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Cпроси Jarvis Botz",
            description=f"Jarvis ответит на: {query}",
            input_message_content=InputTextMessageContent(
                message_text=f"<b>Вопрос: {query}</b>\nJarvis Botz: думаю...",
                parse_mode='HTML'
            ),
            reply_markup=keyboard
            
        )
    ]


    await update.inline_query.answer(results=results, cache_time=300)


async def chosen_query_handler(update: Update, context: CustomTypes):
    chosen_result = update.chosen_inline_result
    query = chosen_result.query

    print("Chosen query:", query)

    if not chosen_result.inline_message_id:
        print("Ошибка: inline_message_id отсутствует!")
        return


    answer = await context.llm.custom_generation(
        prompt_func=get_inline_fast_help_prompt,
        query=query)
    
    try:
        await context.bot.edit_message_text(inline_message_id=chosen_result.inline_message_id,
                                            text=f"<b>Вопрос: {query}</b>\nJarvis Botz: {answer}",
                                      parse_mode='HTML')
    except Exception as e:
        await context.bot.edit_message_text(inline_message_id=chosen_result.inline_message_id,
                                            text=f"Вопрос: {query}\nJarvis Botz: {answer}" + '\n\nСорре, ИИ облажался с форматированием ответа.',)
                                            


async def webapp_data_handler(update: Update, context: CustomTypes):
    data = json.loads(update.effective_message.web_app_data.data)
    context.user_data['session_id'] = data.get('session_id')
    context.user_data['creating_chat'] = False




async def poll_handler(update: Update, context: CustomTypes, ai_answer:str=None):
    chat_id = update.effective_chat.id
    choices = ["⭐️ Ужасно", "⭐️⭐️ Плохо", "⭐️⭐️⭐️ Ок", "⭐️⭐️⭐️⭐️ Хорошо", "⭐️⭐️⭐️⭐️⭐️ Супер"]
    poll_msg = await context.bot.send_poll(chat_id=chat_id, 
                          question='Оцените качество ответа', 
                          options=choices, 
                          is_anonymous=False, 
                          type=Poll.REGULAR)
    
    if 'temporary_answer_grade' not in context.bot_data:
        context.bot_data['temporary_answer_grade'] = {}

    context.bot_data['temporary_answer_grade'][poll_msg.poll.id] = {
        'user_id': update.effective_user.id,
        'answer': ai_answer,
        'chat_id':update.effective_chat.id,
        'message_id':poll_msg.message_id
    }


async def poll_answer_handler(update: Update, context: CustomTypes):
    poll_answer = update.poll_answer

    poll_data = context.bot_data['temporary_answer_grade'].pop(poll_answer.poll_id)

    option = poll_answer.option_ids[0] + 1 #idx4=5star

    poll_data['option'] = option

    if 'global_answer_grade' not in context.bot_data:
        context.bot_data['global_answer_grade'] = {}

    context.bot_data['global_answer_grade'][poll_answer.poll_id] = poll_data

    await context.bot.delete_message(chat_id=poll_data['chat_id'],
                                     message_id=poll_data['message_id'])



async def create_deeplink(update: Update, context: CustomTypes):
    link = helpers.create_deep_linked_url(context.bot.username, payload=str(update.effective_user.id))
    await update.effective_message.reply_text(f'Реферальная ссылка: {link}')



    

async def job_callback(context: CustomTypes):
    chat_id = context.job.chat_id

    text = await get_job_text(context=context, 
                        query=context.user_data['last_query'], 
                        answer=context.user_data['last_answer'])

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def update_job(update: Update, context: CustomTypes, time: int):
    current_jobs = context.job_queue.get_jobs_by_name(str(update.effective_chat.id))

    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        
    context.job_queue.run_once(callback=job_callback, 
                                when=time,
                                chat_id=update.effective_chat.id,
                                user_id=update.effective_user.id,
                                name=str(update.effective_chat.id)
                                )
    


    


