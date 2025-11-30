from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from jarvis_botz.bot.handlers.admin_handlers import dev_command, dev_column, error_handler, promo
from jarvis_botz.bot.handlers.user_handlers import (

                                                generate_answer,
                                                state_token, start,
                                                get_user_user, style,
                                                set_settings, menu_callback, select_callback

                                                )
import os
import logging

from jarvis_botz.config import config
import asyncio
from jarvis_botz.bot.database import Base, engine

import argparse

async def init_db(engine):
    async with engine.begin() as conn:
        # создаёт все таблицы асинхронно
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def parse_args():
    parser = argparse.ArgumentParser(description='bot args')
    parser.add_argument('--stage', type=str, default='dev', help=f'dev or prod', choices=['dev', 'prod'])
    return parser.parse_args()


def main():
    args = parse_args()

    config.stage = getattr(args, 'stage', 'dev')


    if config.stage == 'dev':
        print('developing...')

    if config.stage == 'prod':
        print('producting...')




    asyncio.run(init_db(engine))
    
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)




    app = Application.builder().token(config.telegram_token).build()


    app.add_handler(CommandHandler('start', start))

    # Вместо 'info'
    app.add_handler(MessageHandler(filters.Regex('^ℹ️ Инфо$'), get_user_user))

    # Вместо 'settings'
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Настройки$'), set_settings))

        # Новый Чат
    app.add_handler(MessageHandler(filters.Regex('^🗑️ Новый Чат$'), None))

    # Инструменты
    app.add_handler(MessageHandler(filters.Regex('^🛠️ Инструменты$'), None))


    app.add_handler(CallbackQueryHandler(select_callback, pattern=r'^(\w+):(select|quit):.+$'))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^(\w+):page:\d+$'))



    app.add_handler(CommandHandler('mytokens', state_token))
    app.add_handler(CommandHandler('promo', promo))
    app.add_handler(CommandHandler('columns', dev_column))
    app.add_handler(CommandHandler('base', dev_command))



    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_answer))


    app.add_error_handler(error_handler)

        
    app.run_polling()




if __name__ == '__main__':
    main()


