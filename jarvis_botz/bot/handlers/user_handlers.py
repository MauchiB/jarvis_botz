from telegram import (Update)

from telegram.ext import (ContextTypes, ConversationHandler)
from jarvis_botz.ai.llm import AIGraph
import os


from jarvis_botz.utils import control_tokens, check_user, required_permission, get_profile_text
from jarvis_botz.bot.keyboards import start_keyboard, setting_keyboard_markup, data_items
from jarvis_botz.bot.keyboard_format import PROMPT_CONFIGURATION
from jarvis_botz.utils import create_grid_paged_menu, initialize_new_chat_session, format_user_settings


from telegram.helpers import escape_markdown
from telegram.ext import BasePersistence
from jarvis_botz.bot.contexttypes import CustomTypes


style = 0

import logging
from typing import cast

logger = logging.getLogger(__name__) 

            



@check_user()
async def start(update: Update, context: CustomTypes):
    await update.message.reply_text("Привет! Я Jarvis ваш персональный AI-ассистент. Как я могу служить вам сегодня? (/help для подробной информации)",
                                    reply_markup=start_keyboard)
    


async def time_action(context: CustomTypes):
    pass



async def time_action(update: Update, context: CustomTypes):
    pass

    
from langchain_core.messages import HumanMessage

@check_user(need_chat=True)
@control_tokens(required_tokens=0.5)
async def generate_answer(update: Update, context: CustomTypes):
    model = context.llm

    query = update.effective_message.text

    settings = format_user_settings(user_data=context.user_data, config_map=PROMPT_CONFIGURATION)

    input = {'messages': [HumanMessage(query)]}
    
    config = {
        'configurable': {
        'temperature': settings.get('temperature', 0.7),
        'thread_id': settings.get('current_chat_id'),
                }}
    
    llm_context = {
        'style': settings.get('style', 'helpful assistant'),
        'system_prompt': settings.get('system_prompt', 'mentor'),
        'max_tokens_limit': settings.get('max_tokens', 150),
        'language': settings.get('language', 'english'),
    }
    
    
    msg = await update.effective_message.reply_text('Пишу ответ... ⏳')

    answer = await model.text_generation(msg, llm_context, input, config, streaming=True)

    await msg.edit_text(escape_markdown(answer + "\u200B", 2), parse_mode='MarkdownV2')

    if context.user_data.get('creating_chat', False):
        await initialize_new_chat_session(model, update, context, question=query, answer=answer, session_id=context.user_data['current_chat_id'])
        context.user_data['creating_chat'] = False
        context.user_data['num_chats'] += 1

        


    


@check_user()
async def set_settings(update: Update, context: CustomTypes):
    if update.callback_query:
        await update.callback_query.answer()
        await update.effective_message.edit_text('Выбор настроек для ии:', reply_markup=setting_keyboard_markup)
        return

    await update.effective_message.reply_text('Выбор настроек для ии:', reply_markup=setting_keyboard_markup)
    return style




@check_user()
async def menu_callback(update: Update, context: CustomTypes):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, action, page = args[0], args[1], args[2]
    items = data_items[prefix]
    keyboard = create_grid_paged_menu(all_items=items, prefix=prefix, action='select',
                                      page=int(page), col=2, row=3)
    await update.effective_message.edit_text(f'Choose {prefix} for the bot:', reply_markup=keyboard)


@check_user()
async def setting_select(update: Update, context: CustomTypes):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, action, value = args[0], args[1], args[2]


    if action == 'select':

        if prefix in PROMPT_CONFIGURATION.keys():
            context.user_data[prefix] = value

        else:
            context.user_data[prefix] = value

        await set_settings(update, context)

    if action == 'quit' and value == '_quit_delete':
        await callback.delete_message()
    
    if action == 'quit' and value == '_quit_return':
        await set_settings(update, context)




@check_user()
async def get_user_user(update: Update, context: CustomTypes):
    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)
        user = await user_repo.get_user(id=update.effective_user.id)
        if not user:
            await update.effective_message.reply_text('User isn`t defined')
            return
        
        text = get_profile_text(user, ai_settings=context.user_data)
        await update.effective_message.reply_text(text, parse_mode='HTML')






    


