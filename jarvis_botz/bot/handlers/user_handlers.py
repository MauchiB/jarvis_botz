from telegram import (Update, helpers)


from jarvis_botz.utils import control_tokens, check_user, required_permission, get_profile_text
from jarvis_botz.bot.keyboards import start_keyboard, setting_keyboard_markup, data_items
from jarvis_botz.bot.keyboard_format import PROMPT_CONFIGURATION
from jarvis_botz.utils import create_grid_paged_menu, initialize_new_chat_session, format_user_settings


from telegram.helpers import escape_markdown
from telegram.ext import BasePersistence
from jarvis_botz.bot.contexttypes import CustomTypes
from telegram import InlineKeyboardMarkup

from jarvis_botz.bot.jobs import update_job, poll_handler
import random

import traceback
import time
from typing import List
from io import BytesIO
import base64







@check_user(add_ref=True)
async def start(update: Update, context: CustomTypes):
    await update.message.reply_text(f"Привет! Я Jarvis ваш персональный AI-ассистент. Как я могу служить вам сегодня? (/help для подробной информации)",
                                    reply_markup=start_keyboard)
    


    
from langchain_core.messages import HumanMessage

from PIL import Image


async def prepare_text_for_llm(update: Update, context: CustomTypes) -> List[str]:
    if update.effective_message.text:

        query = [{'type':'text', 
                 'text': update.effective_message.text}]
    
    elif update.effective_message.photo:
        photo = update.effective_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        caption = update.effective_message.caption or ''

        img = Image.open(BytesIO(img_bytes))
        img.thumbnail((256, 256))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75, optimize=True)
        

        encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')

        query = [
                {"type": "text", "text": caption},
                {
                    "type": "image",
                    "base64": encoded_string,
                    "mime_type": "image/jpeg",
                },
            ]
        
    return query




@check_user(need_chat=True)
@control_tokens(required_tokens=1.0)
async def generate_answer(update: Update, context: CustomTypes):
    user = update.effective_user
    message = update.effective_message
    query = await prepare_text_for_llm(update, context)
    model = context.llm


    is_creating = context.user_data.get('creating_chat', False)
    session_id = context.user_data.get('session_id')



    if not is_creating and not session_id:
        await message.reply_text('У вас нет активного чата. Пожалуйста, выберите или создайте чат.')
        return


    try:
        if is_creating:
            # Используем настройки из user_data для нового чата
            raw_settings = context.user_data.get('ai_settings', {})
        else:
            raw_settings = await context.chat_repo.get_chat_metadata(
                user_id=user.id, 
                session_key=session_id
            )




        chat_params = format_user_settings(
            user_data=raw_settings.get('ai_settings', raw_settings), 
            config_map=PROMPT_CONFIGURATION
        )

    except Exception as e:
        print(f"Error fetching metadata: {e}")
        await message.reply_text("Ошибка при загрузке настроек чата.")
        return
    




    config = {
        'configurable': {
            
            'thread_id': session_id,
            'model':chat_params.get('model', 'openai/gpt-5-mini'),
            'model_provider':chat_params.get('model_provider', 'openai'),
            'temperature': chat_params.get('temperature', 0.7),

            'context': {

                'style': chat_params.get('style', 'Catchy helpful assistant'),
                'system_prompt': chat_params.get('system_prompt', 'You are a helpful assistant.'),
                'max_tokens': chat_params.get('max_tokens', 150),
                'language': chat_params.get('language', 'russia'),
                'model':chat_params.get('model', 'models/gpt-5-mini'),

            }

        }
    }
    

    llm_context = config['configurable']

    status_msg = await message.reply_text('Пишу ответ... ⏳')
    
    try:
        answer = await model.text_generation(
            status_msg, 
            llm_context, 
            {'messages': [HumanMessage(content=query)]}, 
            config, 
            streaming=True
        )
        

        final_text = answer + "\u200B"
        try:
            await status_msg.edit_text(final_text, parse_mode='HTML')
        except Exception as e:
            await status_msg.edit_text(f"{final_text} \n\n Ошибка при форматировании ответа.")
        

    except Exception as e:
        print(f"Generation error: {e}")
        print(traceback.print_exc())
        await status_msg.edit_text("Произошла ошибка при генерации ответа. Попробуйте позже.")
        return


    try:
        if is_creating:
            await initialize_new_chat_session(
                update, context, 
                query=query, answer=answer, 
                session_id=session_id
            )
            context.user_data['creating_chat'] = False
            context.user_data['num_chats'] = context.user_data.get('num_chats', 0) + 1

        else:
            current_messages_count = raw_settings.get('num_messages', 0)
            
            new_metadata = {
                'last_interaction': time.time(),
                'num_messages': current_messages_count + 1,
                'last_query': query,
                'last_answer': answer,
                'model': config['model']
            }
            
            await context.chat_repo.update_chat_metadata(
                user_id=user.id,
                session_key=session_id,
                metadata=new_metadata
            )


        context.user_data.update({
            'last_query': query,
            'last_answer': answer
        })
        
        # Обновляем задачу очистки/сохранения
        update_job(update, context, 60*60*24)
        
    except Exception as e:
        print(f"Database update error: {e}")

    # 6. Дополнительные фичи (опрос)
    if random.random() < 0.05:
        await poll_handler(update=update, context=context, ai_answer=answer)


    


@check_user()
async def set_settings(update: Update, context: CustomTypes):
    if update.callback_query:
        await update.callback_query.answer()
        await update.effective_message.edit_text('Выбор настроек для ии:', reply_markup=setting_keyboard_markup)
        return

    await update.effective_message.reply_text('Выбор настроек для ии:', reply_markup=setting_keyboard_markup)





@check_user()
async def menu_callback(update: Update, context: CustomTypes):
    callback = update.callback_query
    if callback:
        await callback.answer()
        args = callback.data.split(':')
        prefix, action, page = args[0], args[1], args[2]
    else:
        prefix = 'set_model'
        page = 0


    items = data_items[prefix]
    keyboard = create_grid_paged_menu(all_items=items, prefix=prefix, action='select',
                                      page=int(page), col=1, row=5, quit_button='_quit_delete')
    if callback:
        await update.effective_message.edit_text(f'Выберите {prefix} для бота:', reply_markup=keyboard)
    else:
        await update.effective_message.reply_text(f'Выберите {prefix} для бота:', reply_markup=keyboard)


@check_user()
async def select_callback(update: Update, context: CustomTypes):
    callback = update.callback_query
    await callback.answer()
    args = callback.data.split(':')
    prefix, action, value = args[0], args[1], args[2]


    if action == 'select':
        context.user_data['ai_settings'][prefix] = value
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
        
        text = get_profile_text(user, ai_settings=context.user_data['ai_settings'])
        await update.effective_message.reply_text(text, parse_mode='HTML')






    


