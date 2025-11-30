from telegram import (Update)

from telegram.ext import (ContextTypes, ConversationHandler)
from jarvis_botz.ai.graph import graph
import os
import dotenv

from jarvis_botz.bot.database import add_user, get_user, _set_attr
from jarvis_botz.utils import require_start, get_attr_table, check_user
from jarvis_botz.bot.keyboards import start_keyboard, setting_keyboard_markup, data_items, create_grid_paged_menu

from telegram.helpers import escape_markdown


style = 0


import logging
import redis

logger = logging.getLogger(__name__) 
            



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user:
        user = await add_user(update.effective_user.id, update.effective_user.username)

    await update.message.reply_text("Hello! I'm Jarvis Botz. How can I serve to you today?",
                                    reply_markup=start_keyboard)
    


        
@require_start
async def generate_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check = await check_user(type='TEXT', id=update.effective_user.id)
    if isinstance(check, str):
        await update.effective_message.reply_text(f'{check}')
        return
    

    await _set_attr(id=update.effective_user.id, column='tokens', value=check.tokens - 0.5)

    msg = await update.effective_message.reply_text('Typing...')

    input = {
        'style': context.user_data.get('style', 'helpful assistant'),
        'input': update.effective_message.text}
    
    config = {
        'configurable': {
        'temperature': context.user_data.get('temperature', 0.7),
        'session_id': str(update.effective_user.id)}
                }

    await graph._text_generation(msg, update, context, input, config, streaming=True)
    
    await msg.edit_text(escape_markdown(context.user_data['last_sent_text'] + "\u200B", 1), parse_mode='Markdown')




    


@require_start
async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text('Choose options:', reply_markup=setting_keyboard_markup)
    return style


@require_start
async def quit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text('Choose options:', reply_markup=setting_keyboard_markup)
    return style


@require_start
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, page = args[0], args[2]
    items = data_items[prefix]
    keyboard = create_grid_paged_menu(all_items=items, prefix=prefix, page=int(page), col=2, row=3)
    await update.effective_message.edit_text(f'Choose {prefix} for the bot:', reply_markup=keyboard)


@require_start
async def select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, action, value = args[0], args[1], args[2]

    if action == 'select':
        context.user_data[prefix] = value

    if action == 'quit' and value == 'start':
        await callback.delete_message()
    
    else: #action == 'quit' and value == 'select':
        await update.effective_message.edit_text('Choose options:', reply_markup=start_keyboard)





@require_start
async def state_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
     user = await get_user(update.effective_user.id)
     await update.effective_message.reply_text(f'You have {user.tokens} tokens')




@require_start
async def get_user_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(id=update.effective_user.id)
    if not user:
        await update.effective_message.reply_text('User isn`t defined')
        return
    
    text = get_attr_table(user)
    await update.effective_message.reply_text(f'INFORMATION: \n{text}')






    


