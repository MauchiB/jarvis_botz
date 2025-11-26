from telegram import Update
from telegram.ext import (ContextTypes, ConversationHandler)
from jarvis_botz.ai.graph import graph
import os
import dotenv


from jarvis_botz.bot.database import add_token, add_user, remove_token, get_user, change_role
from jarvis_botz.utils import admin_require, require_start, check_user, get_attr_table



@admin_require
@require_start
async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(username=context.args[0])
    if not user:
        await update.effective_message.reply_text('User isn`t defined')
        return
    
    add_token(user.id, float(context.args[1]))

    await update.effective_message.reply_text(f'Done!')





@admin_require
@require_start
async def get_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return 
    
    user = get_user(username=context.args[0])
    if not user:
        await update.effective_message.reply_text('User isn`t defined')
        return
    
    text = get_attr_table(user)

    await update.effective_message.reply_text(f'INFORMATION: \n{text}')



@admin_require
@require_start
async def change_user_role(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not len(context.args) == 2:
        return 
    
    user = get_user(username=context.args[0])
    if not user:
        await update.effective_message.reply_text('User isn`t defined')
        return

    change_role(username=context.args[0], role=context.args[1])

    await update.effective_message.reply_text(f'Done!')