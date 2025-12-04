from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from jarvis_botz.utils import create_grid_paged_menu
import os
from typing import List, Tuple

from jarvis_botz.bot.database import get_redis_client, get_chat_redis, create_chat_redis, delete_chat_redis, get_all_chats_redis
from jarvis_botz.utils import required_permission, check_user, control_tokens, get_attr_table
from uuid import uuid4
import time


state_chat_name = 5



def chat_create_button_action(session_id:str) -> List[InlineKeyboardButton]:
    chat_inline = [
    # Ряд 1: Основные действия (Удалить и Выбрать)
    [
        InlineKeyboardButton("🗑️ Удалить чат", callback_data=f'chat:delete_final:{session_id}'),
        InlineKeyboardButton("✅ Выбрать Чат", callback_data=f'chat:select_final:{session_id}')
    ],

    [
        InlineKeyboardButton("❌ Назад", callback_data=f'chat:quit:_quit_return') 
    ]
           ]
    chat_inline = InlineKeyboardMarkup(chat_inline)
    return chat_inline


@check_user()
async def create_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_chat_id'] = str(uuid4())
    context.user_data['creating_chat'] = True
    await update.message.reply_text("Чат будет создан при первом вашем сообщении в этом чате. (Название чата будет сгенерировано автоматически)")


@check_user()
async def chat_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query

    chat_data = await get_all_chats_redis(prefix_metadata='user_chat_metadata', name=update.effective_user.id)

    if not chat_data:
        if callback:
            await callback.answer()
            await update.effective_message.edit_text("У вас еще нет созданных чатов. Пожалуйста, создайте чат сначала.")
            return
        else:
            await update.effective_message.reply_text("У вас еще нет созданных чатов. Пожалуйста, создайте чат сначала.")
            return
    

    buttons_data = []
    for chat in chat_data.values():
        buttons_data.append( (chat['name'], chat['session_id']) )
    
    
    chat_list = create_grid_paged_menu(all_items=buttons_data, prefix='chat', action='select_action', page=0, col=1, row=5, quit_button='_quit_delete')
    
    if callback:
        await callback.answer()
        await update.effective_message.edit_text(
            "Управление вашими чатами:",
            reply_markup=chat_list
        )
    else:
        await update.message.reply_text(
            "Управление вашими чатами:",
            reply_markup=chat_list
        )



@check_user()
async def chat_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    args = callback.data.split(':')
    prefix, action, value = args[0], args[1], args[2]

    print(prefix, action, value)

    if action == 'select_final':
        context.user_data['current_chat_id'] = value
        await update.effective_message.delete()

    elif action == 'delete_final':
        context.user_data['current_chat_id'] = None
        await delete_chat_redis(prefix_history='user_chat_history', prefix_metadata='user_chat_metadata', user_id=update.effective_user.id, session_id=value)
        await chat_list(update, context)


    elif action == 'quit' and value == '_quit_return':
        await chat_list(update, context)

    elif action == 'quit' and value == '_quit_delete':
        await update.effective_message.delete()


    elif action == 'select_action':
        keyboard = chat_create_button_action(session_id=value)
        await update.effective_message.edit_text("Выберите действие: удалить или выбрать чат.", reply_markup=keyboard)
        await callback.answer()


    await callback.answer()







