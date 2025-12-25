import os
import logging
import argparse
import asyncio
import dotenv
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    CallbackQueryHandler, ContextTypes, PersistenceInput
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Твои импорты
from jarvis_botz.config import Config, DEV_CONFIG
from jarvis_botz.bot.db.schemas import init_db, get_db_engine
from jarvis_botz.bot.db.user_repo import RedisPersistence, UserRepository
from jarvis_botz.bot.contexttypes import CustomTypes
from jarvis_botz.ai.llm import AIGraph

# Импорты хэндлеров
from jarvis_botz.bot.handlers.admin_handlers import dev_command, dev_column, error_handler, promo, error_test_handler
from jarvis_botz.bot.handlers.user_handlers import generate_answer, start, get_user_user, set_settings, menu_callback, setting_select
from jarvis_botz.bot.handlers.chat_handlers import chat_list, chat_select, create_chat

dotenv.load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='bot args')
    parser.add_argument('--stage', type=str, default='dev', choices=['dev', 'prod'])
    return parser.parse_args()

def setup_handlers(app: Application):
    """Регистрируем все обработчики в одном месте."""
    app.add_handler(CommandHandler('start', start))
    
    # Текстовые кнопки меню
    app.add_handler(MessageHandler(filters.Regex('^ℹ️ Инфо$'), get_user_user))
    app.add_handler(MessageHandler(filters.Regex('^⚙️ Настройки$'), set_settings))
    app.add_handler(MessageHandler(filters.Regex('^🗑️ Чаты$'), chat_list))
    app.add_handler(MessageHandler(filters.Regex('^➕ Создать новый чат$'), create_chat))
    
    # Callback-и для чатов
    app.add_handler(CallbackQueryHandler(chat_list, pattern=r'^chat:page:\d+$'))
    app.add_handler(CallbackQueryHandler(chat_select, pattern=r'^chat:(\w+):.+$'))

    # Callback-и для настроек
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^(\w+):page:\d+$'))
    app.add_handler(CallbackQueryHandler(setting_select, pattern=r'^(\w+):(\w+):.+$'))

    # Админские команды
    app.add_handler(CommandHandler('promo', promo))
    app.add_handler(CommandHandler('columns', dev_column))
    app.add_handler(CommandHandler('base', dev_command))
    app.add_handler(CommandHandler('error', error_test_handler))

    # Основной обработчик текста (LLM)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_answer))
    
    # Ошибки
    app.add_error_handler(error_handler)

async def start_bot():
    """Главная асинхронная функция запуска."""
    args = parse_args()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    # 1. Загрузка конфига
    if args.stage == 'dev':
        cfg = Config(telegram_token=os.getenv('TELEGRAM_BOT_TOKEN'), stage=args.stage, **DEV_CONFIG)
    else:
        cfg = Config(telegram_token=os.getenv('TELEGRAM_BOT_TOKEN'), stage=args.stage)

    print(f"🚀 Starting bot in {args.stage} mode...")

    # 2. Инициализация Redis Persistence (асинхронно)
    # Это важно сделать ДО создания Application
    persistence = await RedisPersistence.create(cfg=cfg, store_data=PersistenceInput(bot_data=False))

    # 3. Настройка ContextTypes
    context_types = ContextTypes(context=CustomTypes)

    # 4. Сборка Application
    app = (
        Application.builder()
        .token(cfg.telegram_token)
        .context_types(context_types)
        .persistence(persistence) # Передаем наш RedisPersistence сюда
        .build()
    )

    # 5. Инициализация БД, LLM и прочих асинхронных штук
    engine = get_db_engine(cfg=cfg)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autoflush=True, expire_on_commit=False)
    await init_db(engine)
    
    llm = await AIGraph.create(cfg=cfg)

    # 6. Заполняем bot_data (чтобы всё было доступно через context)
    app.bot_data['chat_repo'] = persistence
    app.bot_data['user_repo'] = UserRepository # если это класс, можно добавить .create(), если нужно
    app.bot_data['llm'] = llm
    app.bot_data['session_factory'] = SessionLocal

    # 7. Настройка хэндлеров
    setup_handlers(app)


    print(app.bot_data)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()


    while True:
        await asyncio.sleep(3600)



if __name__ == '__main__':
    try:

        app = asyncio.run(start_bot())

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ CRITICAL ERROR: {e}")