from telegram import Update
from telegram.ext import (ContextTypes, ConversationHandler)
import os
import dotenv

from sqlalchemy import Integer,Boolean, String, Numeric

from jarvis_botz.bot.db.user_repo import UserRepository
from jarvis_botz.utils import required_permission, check_user, set_type
from jarvis_botz.bot.db.user_repo import User
from jarvis_botz.bot.log_bot import logger
from jarvis_botz.bot.contexttypes import CustomTypes

import traceback


@check_user()
@required_permission(['developer'], need_alert=True)
async def dev_column(update: Update, context: CustomTypes):
    columns = [f'*{column.name}*: {column.type}' for column in User.__table__.columns]
    await update.effective_message.reply_text(f'**All column of database**:\n{'\n'.join(columns)}', parse_mode='Markdown')

    



@check_user()
@required_permission(['developer'], need_alert=True)
async def dev_command(update: Update, context: CustomTypes):
    args = context.args

    if len(args) < 3 or len(args) > 4:
        await update.effective_message.reply_text('Need 3 to 4 arguments: <username> <set or get> <column> if set: <value>')
        return

    username = args[0]
    action = args[1]
    column = args[2]


    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)
        user = await user_repo.get_user(username=username)

        
        try:
            if action == 'set':
                value = args[3]
                value = await set_type(column, value)

                update_data = {column:value}

                await user_repo._set_attr(username=username, update_data=update_data)
                await update.effective_message.reply_text(f'{username}: {column}={value}')
                return

            elif action == 'get':
                attr = getattr(user, column, 'Attribute was not found')
                await update.effective_message.reply_text(f'Attr - {attr}')
                return

            else:
                await update.effective_message.reply_text('First argument need to be (set or get)')

            await update.effective_message.reply_text(f'Success!')

        except Exception as error:
            await update.effective_message.reply_text(f'Something goes wrong')
            return error
    



@check_user()
@required_permission(['developer'], need_alert=False)
async def error_handler(update: Update, context: CustomTypes):
    logger.error('Something goes wrong...', context.error, exc_info=True)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    async with context.bot_data['session_factory']() as session:
        rep = UserRepository(session=session)
        users = await rep.get_users_by_role(role='developer')
        if users:
            for user in users:
                await context.bot.send_message(user.chat_id, tb_string[-1000:])



@check_user()
@required_permission(['developer'], need_alert=True)
async def error_test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raise ValueError('error test')




@check_user()
async def promo(update: Update, context: CustomTypes):
    admin_promo = os.getenv('ADMIN_PROMO')
    dev_promo = os.getenv('DEV_PROMO')

    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)

        if not context.args:
            return

        if context.args[0] == admin_promo:
            await user_repo._set_attr(id=update.effective_user.id, update_data={'role':'admin'})

        elif context.args[0] == dev_promo:

            await user_repo._set_attr(id=update.effective_user.id, update_data={'role':'developer'})

        else:
            await update.effective_message.reply_text('Something goes wrong')



