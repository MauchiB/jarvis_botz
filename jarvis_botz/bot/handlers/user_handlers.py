from telegram import Update
from telegram.ext import (ContextTypes, ConversationHandler)
from jarvis_botz.ai.graph import graph
import os
import dotenv

from jarvis_botz.bot.database import add_token, add_user, remove_token, get_user, change_role
from jarvis_botz.utils import require_start, get_attr_table, check_user
from telegram.helpers import escape_markdown



style = 0


import logging
import redis

logger = logging.getLogger(__name__) 
            
        
@require_start
async def generate_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check = await check_user(type='TEXT', id=update.effective_user.id)
    if check:
        await update.effective_message.reply_text(f'{check}')
        return
    

    await remove_token(id=update.effective_user.id, num=0.5)

    collected_text = ''
    last_sent_text = ''

    msg = await update.effective_message.reply_text('Typing...')


    async for out in graph.model.astream({
        'input': update.effective_message.text,
        'style': context.user_data.get('style', 'helpful assistant')},
        
        config={'configurable':{'session_id': update.effective_user.id}}
        ):
        
        collected_text += out.content


        if len(collected_text) > len(last_sent_text): 
            try:
                await msg.edit_text(collected_text)
                last_sent_text = collected_text # Обновляем последний отправленный текст
            except Exception as e:
                pass

    
    
    await msg.edit_text(collected_text)

    


@require_start
async def set_style_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text('Write the style you want to see in Jarvis Botz responses:')
    return style





@require_start
async def set_style_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text
    context.user_data['style'] = text
    await update.effective_message.reply_text(f'Style set to: {text}')
    return ConversationHandler.END



@require_start
async def cancel_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text('Style setting cancelled.')
    return ConversationHandler.END



@require_start
async def state_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
     user = await get_user(update.effective_user.id)
     await update.effective_message.reply_text(f'You have {user.tokens} tokens')


        


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.effective_user.id)
    if not user:
        print('user')
        user = await add_user(update.effective_user.id, update.effective_user.username)

    await update.message.reply_text("Hello! I'm Jarvis Botz. How can I assist you today? \n Use 'jarvis <your question>' to interact with me.")



@require_start
async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_promo = os.getenv('ADMIN_PROMO')
    dev_promo = os.getenv('DEV_PROMO')

    if not context.args:
        return


    if context.args[0] == admin_promo:
        await change_role(update.effective_user.id, role='admin')

    elif context.args[0] == dev_promo:
        await change_role(update.effective_user.id, role='developer')

    else:
        await update.effective_message.reply_text('Something goes wrong')





@require_start
async def get_user_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(id=update.effective_user.id)
    if not user:
        await update.effective_message.reply_text('User isn`t defined')
        return
    
    text = get_attr_table(user)

    await update.effective_message.reply_text(f'INFORMATION: \n{text}')





    


