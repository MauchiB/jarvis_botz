import os
import logging
import argparse
import asyncio
import dotenv
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    CallbackQueryHandler, ContextTypes, PersistenceInput, TypeHandler, PollAnswerHandler, InlineQueryHandler, ChosenInlineResultHandler,
    PreCheckoutQueryHandler, ConversationHandler
)
from telegram import Update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

# Твои импорты
from jarvis_botz.config import Config, DEV_CONFIG
from jarvis_botz.bot.db.schemas import init_db, get_db_engine
from jarvis_botz.bot.db.user_repo import RedisPersistence, UserRepository
from jarvis_botz.bot.contexttypes import CustomTypes, CustomApplication
from jarvis_botz.ai.llm import AIGraph



# Импорты хэндлеров
from jarvis_botz.bot.handlers.admin_handlers import dev_command, dev_column, error_handler, promo, error_test_handler
from jarvis_botz.bot.handlers.user_handlers import (generate_answer, start, 
                                                    get_user_user, set_settings, 
                                                    menu_callback, select_callback)

from jarvis_botz.bot.jobs import create_deeplink, poll_answer_handler, webapp_data_handler, query_handler, chosen_query_handler
from jarvis_botz.bot.handlers.chat_handlers import chat_list, chat_select, create_chat
from jarvis_botz.bot.handlers.payments_handler import start_payment_1, start_payment_2, precheckout_callback, successful_payment_callback, refund_payment_callback, state_payment
from jarvis_botz.web.backend.main import start_backend
import threading
dotenv.load_dotenv()

app: CustomApplication = None

def parse_args():
    parser = argparse.ArgumentParser(description='bot args')
    parser.add_argument('-t', '--token', type=str)
    parser.add_argument('--stage', type=str, default='dev', choices=['dev', 'prod'])
    parser.add_argument('-w', '--webhook', type=str, help='webhook url')
    parser.add_argument('-wp', '--webhook_path', type=str, default='webhook', help='webhook path')
    return parser.parse_args()

def setup_handlers(app: Application):
    """Регистрируем все обработчики в одном месте."""



    #app.add_handler(TypeHandler(Update, register_user), group=-1)

    app.add_handler(CommandHandler('start', start))

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))

    app.add_handler(PollAnswerHandler(poll_answer_handler))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^💎 Купить токены$'), start_payment_1)],
        states={
            state_payment: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_payment_2)]
        },
        fallbacks=[],
        name="payment_conversation",
        persistent=True
    ))

    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(CommandHandler('refund', refund_payment_callback))


    app.add_handler(InlineQueryHandler(query_handler))

    app.add_handler(ChosenInlineResultHandler(chosen_query_handler))

    app.add_handler(CommandHandler('ref', create_deeplink))

    
    # Текстовые кнопки меню
    app.add_handler(MessageHandler(filters.Regex('^🤖 Выбрать ИИ$'), menu_callback))
    app.add_handler(MessageHandler(filters.Regex('^ℹ️ Инфо$'), get_user_user))
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Настройки$'), set_settings))
    app.add_handler(MessageHandler(filters.Regex('^🗑️ Чаты$'), chat_list))
    app.add_handler(MessageHandler(filters.Regex('^➕ Создать новый чат$'), create_chat))
    
    # Callback-и для чатов
    app.add_handler(CallbackQueryHandler(chat_list, pattern=r'^chat:page:\d+$'))
    app.add_handler(CallbackQueryHandler(chat_select, pattern=r'^chat:(\w+):.+$'))

    # Callback-и для настроек
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^(\w+):page:\d+$'))
    app.add_handler(CallbackQueryHandler(select_callback, pattern=r'^(\w+):(\w+):.+$'))

    # Админские команды
    app.add_handler(CommandHandler('promo', promo))
    app.add_handler(CommandHandler('columns', dev_column))
    app.add_handler(CommandHandler('base', dev_command))
    app.add_handler(CommandHandler('error', error_test_handler))

    # Основной обработчик текста (LLM)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.PHOTO, generate_answer))
    
    # Ошибки
    app.add_error_handler(error_handler)

async def start_bot():
    """Главная асинхронная функция запуска."""
    args = parse_args()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    cfg_args = vars(args)

    if args.stage == 'dev':
        cfg_args.update(DEV_CONFIG)
    
    cfg = Config(**cfg_args)

    print(f"🚀 Starting bot in {args.stage} mode...")

    # 2. Инициализация Redis Persistence (асинхронно)
    # Это важно сделать ДО создания Application
    persistence = await RedisPersistence.create(cfg=cfg, store_data=PersistenceInput(bot_data=False))

    # 3. Настройка ContextTypes
    context_types = ContextTypes(context=CustomTypes)

    # 4. Сборка Application
    global app

    app = (
        CustomApplication.builder()
        .token(cfg.telegram_token)
        .context_types(context_types)
        .persistence(persistence)
        .build()
    )

    # 5. Инициализация БД, LLM и прочих асинхронных штук
    engine = get_db_engine(cfg=cfg)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autoflush=True, expire_on_commit=False)
    await init_db(engine)
    
    llm = await AIGraph.create(cfg=cfg)
     

    '''
    job = app.job_queue

    job.run_repeating(llm.set_access_token, 25*60)
    '''




    app.chat_repo = persistence
    app.user_repo = UserRepository
    app.llm = llm
    app.session_factory = SessionLocal


    setup_handlers(app)



    from jarvis_botz.web.backend.main import web_app
    # 2. Прокидываем бота в state FastAPI
    web_app.state.bot_app = app
    web_app.state.cfg = cfg

    # 3. Настраиваем конфиг сервера
    config = uvicorn.Config(
        app=web_app, 
        host="127.0.0.1", 
        port=8000, 
        loop="asyncio" # Явно указываем использовать текущий loop
    )
    server = uvicorn.Server(config)


    await app.initialize()
    if app.updater:
        await app.updater.initialize()


    try:
        await asyncio.gather(
            app.start(),
            app.updater.start_webhook(listen='0.0.0.0',
                                    port=80,
                                    url_path=cfg.WEBHOOK_PATH,
                                    webhook_url=f'{cfg.WEBHOOK_URL}{cfg.WEBHOOK_PATH}'),  
            server.serve()
        )
    finally:
        await app.stop()
        await app.shutdown()
        print("Бот и сервер остановлены корректно.")




if __name__ == '__main__':
    try:

        app = asyncio.run(start_bot())

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ CRITICAL ERROR: {e}")