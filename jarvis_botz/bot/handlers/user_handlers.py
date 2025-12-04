from telegram import (Update)

from telegram.ext import (ContextTypes, ConversationHandler)
from jarvis_botz.ai.graph import graph
import os
import dotenv

from jarvis_botz.bot.database import add_user, get_user, _set_attr, get_chat_redis
from jarvis_botz.utils import control_tokens, check_user, required_permission, get_attr_table
from jarvis_botz.bot.keyboards import start_keyboard, setting_keyboard_markup, data_items
from jarvis_botz.utils import create_grid_paged_menu, initialize_new_chat_session


from telegram.helpers import escape_markdown
from telegram.ext import BasePersistence


style = 0

import logging

logger = logging.getLogger(__name__) 

            



@check_user()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Jarvis ваш персональный AI-ассистент. Как я могу служить вам сегодня? (/help для подробной информации)",
                                    reply_markup=start_keyboard)
    


@check_user(need_chat=True)
@control_tokens(required_tokens=0.5)
async def generate_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    input = {
        'style': context.user_data.get('style', 'helpful assistant'),
        'input': update.effective_message.text}
    
    config = {
        'configurable': {
        'temperature': context.user_data.get('temperature', 0.7),
        'session_id': context.user_data.get('current_chat_id'),
                }}
    
    msg = await update.effective_message.reply_text('Пишу ответ... ⏳')

    answer = await graph.text_generation(msg, update, context, input, config, streaming=True)

    await msg.edit_text(escape_markdown(answer + "\u200B", 2), parse_mode='MarkdownV2')

    if context.user_data.get('creating_chat', False):
        await initialize_new_chat_session(update, context, question=input['input'], answer=answer, session_id=context.user_data['current_chat_id'])
        context.user_data['creating_chat'] = False

        





    


@check_user()
async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.effective_message.edit_text('Choose options:', reply_markup=setting_keyboard_markup)
        return

    await update.effective_message.reply_text('Choose options:', reply_markup=setting_keyboard_markup)
    return style



@check_user()
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, action, page = args[0], args[1], args[2]
    items = data_items[prefix]
    keyboard = create_grid_paged_menu(all_items=items, prefix=prefix, action='select',
                                      page=int(page), col=2, row=3)
    await update.effective_message.edit_text(f'Choose {prefix} for the bot:', reply_markup=keyboard)


@check_user()
async def setting_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, action, value = args[0], args[1], args[2]


    if action == 'select':
        context.user_data[prefix] = value
        await set_settings(update, context)

    if action == 'quit' and value == '_quit_delete':
        await callback.delete_message()
    
    if action == 'quit' and value == '_quit_return':
        await set_settings(update, context)







@check_user()
async def state_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
     user = await get_user(update.effective_user.id)
     await update.effective_message.reply_text(f'You have {user.tokens} tokens')




@check_user()
async def get_user_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(id=update.effective_user.id)
    if not user:
        await update.effective_message.reply_text('User isn`t defined')
        return
    
    text = get_attr_table(user)
    await update.effective_message.reply_text(f'INFORMATION: \n{text}')






    


