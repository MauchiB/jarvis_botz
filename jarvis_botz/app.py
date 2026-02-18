import asyncio
import logging
import dotenv
import uvicorn

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    PollAnswerHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    PreCheckoutQueryHandler,
    ConversationHandler,
    filters,
)

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession


from jarvis_botz.config import Config
from jarvis_botz.bot.db.schemas import init_db, get_db_engine
from jarvis_botz.bot.db.user_repo import RedisPersistence, UserRepository
from jarvis_botz.bot.contexttypes import CustomTypes, CustomApplication
from jarvis_botz.ai.llm import AIGraph

from jarvis_botz.bot.handlers.admin_handlers import (
    dev_command,
    dev_column,
    error_handler,
    promo,
    error_test_handler,
)

from jarvis_botz.bot.handlers.user_handlers import (
    start,
    ai_settings_menu_handler,
    choose_setting_menu_callback,
    apply_setting_choice_callback,
    reset_settings_callback,
    user_info_handler,
    help_handler,
)

from jarvis_botz.bot.handlers.ai_generation_handler import generate_answer_handler

from jarvis_botz.bot.jobs import (
    create_deeplink,
    poll_answer_handler,
    webapp_data_handler,
    query_handler,
    chosen_query_handler,
)

from jarvis_botz.bot.handlers.chat_handlers import chat_list, chat_select, create_chat
from jarvis_botz.bot.handlers.payments_handler import (
    start_payment,
    wait_stars,
    precheckout_callback,
    successful_payment_callback,
    refund_payment_callback,
    PaymentState
)


dotenv.load_dotenv()


def setup_handlers(app: Application) -> None:
    # --- USER ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("ref", create_deeplink))

    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler))
    app.add_handler(PollAnswerHandler(poll_answer_handler))

    app.add_handler(InlineQueryHandler(query_handler))
    app.add_handler(ChosenInlineResultHandler(chosen_query_handler))

    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Инфо$"), user_info_handler))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Настройки$"), ai_settings_menu_handler))
    app.add_handler(MessageHandler(filters.Regex("^🗑️ Чаты$"), chat_list))
    app.add_handler(MessageHandler(filters.Regex("^➕ Создать новый чат$"), create_chat))

    # --- PAYMENTS ---
    app.add_handler(
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^💎 Купить токены$"), start_payment)],
            states={
                PaymentState.WAIT_STARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_stars)]
            },
            fallbacks=[],
            name="payment_conversation",
            persistent=True,
        )
    )

    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(CommandHandler("refund", refund_payment_callback))

    # --- CALLBACKS ---
    app.add_handler(CallbackQueryHandler(reset_settings_callback, pattern=r"^settings:reset:_reset_settings$"))
    app.add_handler(CallbackQueryHandler(chat_list, pattern=r"^chat:page:\d+$"))
    app.add_handler(CallbackQueryHandler(chat_select, pattern=r"^chat:(\w+):.+$"))

    app.add_handler(CallbackQueryHandler(choose_setting_menu_callback, pattern=r"^(\w+):page:\d+$"))
    app.add_handler(CallbackQueryHandler(apply_setting_choice_callback, pattern=r"^(\w+):(\w+):.+$"))

    # --- ADMIN ---
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("columns", dev_column))
    app.add_handler(CommandHandler("base", dev_command))
    app.add_handler(CommandHandler("error", error_test_handler))

    # --- LLM ---
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND | filters.PHOTO | filters.Document.ALL,
            generate_answer_handler,
        )
    )

    # --- ERRORS ---
    app.add_error_handler(error_handler)





async def build_application(cfg: Config) -> CustomApplication:
    persistence = await RedisPersistence.create(cfg=cfg)

    context_types = ContextTypes(context=CustomTypes)

    app = (
        CustomApplication.builder()
        .token(cfg.telegram.token)
        .context_types(context_types)
        .persistence(persistence)
        .build()
    )

    app.chat_repo = persistence
    app.user_repo_class = UserRepository

    return app




async def init_services(app: CustomApplication, cfg: Config):
    engine = get_db_engine(cfg=cfg)
    session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=True,
        expire_on_commit=False,
    )

    await init_db(engine)
    llm = await AIGraph.create(cfg=cfg)

    app.session_factory = session_factory
    app.llm = llm



def build_web_server(app, cfg: Config):
    from jarvis_botz.web.backend.main import web_app

    web_app.state.bot_app = app
    web_app.state.cfg = cfg

    config = uvicorn.Config(
        app=web_app,
        host=cfg.server.host,
        port=cfg.server.port,
        loop="asyncio",
    )

    return uvicorn.Server(config)




async def start_bot():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    cfg = Config.from_env()

    app = await build_application(cfg)
    await init_services(app, cfg)

    setup_handlers(app)
    server = build_web_server(app, cfg)

    await app.initialize()
    if app.updater:
        await app.updater.initialize()

    try:
        await asyncio.gather(
            app.start(),
            app.updater.start_webhook(
                listen='0.0.0.0',
                port=cfg.telegram.webhook_port,
                url_path=cfg.telegram.webhook_path,
                webhook_url=f"{cfg.telegram.webhook_url}{cfg.telegram.webhook_path}",
            ),
            server.serve(),
        )
    finally:
        await app.stop()
        await app.shutdown()
        logging.info("Bot stopped correctly.")



def main():
    try:
        asyncio.run(start_bot())
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n❌ CRITICAL ERROR: {e}")


if __name__ == "__main__":
    main()
