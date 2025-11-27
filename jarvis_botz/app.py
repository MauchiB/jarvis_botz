from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from jarvis_botz.bot.handlers.admin_handlers import get_user_handler, set_token, change_user_role
from jarvis_botz.bot.handlers.user_handlers import (generate_answer, set_style_1,
                                                set_style_2, cancel_style,
                                                state_token, start, promo,
                                                get_user_user, style)
import os
import logging

from jarvis_botz.config import config
import asyncio
from jarvis_botz.bot.database import Base, engine


async def init_db(engine):
    async with engine.begin() as conn:
        # создаёт все таблицы асинхронно
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(init_db(engine))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)



app = Application.builder().token(config.telegram_token).build()


app.add_handler(CommandHandler('start', start))

app.add_handler(

    ConversationHandler(
    entry_points=[CommandHandler('setstyle', set_style_1)],
    states={
        style: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_style_2)]
    },
    fallbacks=[CommandHandler('cancel', cancel_style)]
    )

    )


app.add_handler(CommandHandler('mytokens', state_token))
app.add_handler(CommandHandler('settokens', set_token))
app.add_handler(CommandHandler('promo', promo))
app.add_handler(CommandHandler('getuser', get_user_handler))
app.add_handler(CommandHandler('info', get_user_user))
app.add_handler(CommandHandler('change', change_user_role))





app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_answer))

    

app.run_polling()



