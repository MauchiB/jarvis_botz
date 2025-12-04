from telegram import Update
from telegram.ext import (ContextTypes, ConversationHandler)
from jarvis_botz.ai.graph import graph
import os
import dotenv

from sqlalchemy import Integer,Boolean, String, Numeric

from jarvis_botz.bot.database import get_user, _set_attr
from jarvis_botz.utils import required_permission, check_user
from jarvis_botz.bot.database import User
from jarvis_botz.bot.log_bot import logger
import traceback


@check_user()
@required_permission(['developer'], need_alert=True)
async def dev_column(update: Update, context: ContextTypes.DEFAULT_TYPE):
    columns = [f'*{column.name}*: {column.type}' for column in User.__table__.columns]
    await update.effective_message.reply_text(f'**All column of database**:\n{'\n'.join(columns)}', parse_mode='Markdown')



def set_type(column_name: str, input_value: str):

    try:
        column = getattr(User, column_name)
    except AttributeError:
        raise ValueError(f"Column: {column_name} don`t found")
        
    column_type = column.type
    lower_value = input_value.lower()


    if isinstance(column_type, Boolean):
        lower_value = input_value.lower()
        if lower_value in ['true', '1']:
            return True
        elif lower_value in ['false', '0']:
            return False
        else:
            raise ValueError(f"{input_value} - need to be bool object (true or 1 / false or 0)")

    elif isinstance(column_type, Integer):
        try:
            return int(input_value)
        except ValueError:
            raise ValueError(f"{input_value} - need to be int object (any number)")


    elif isinstance(column_type, Numeric):
        try:
            return float(input_value)
        except ValueError:
            raise ValueError(f"{input_value} - need to be numeric object like (float)")


    elif isinstance(column_type, String):
        try:
            return str(input_value)
        except ValueError:
            raise ValueError(f"{input_value} - need to be str object (any text)")
        

    



@check_user()
@required_permission(['developer'], need_alert=True)
async def dev_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if len(args) < 3 or len(args) > 4:
        await update.effective_message.reply_text('Need 3 to 4 arguments: <username> <set or get> <column> if set: <value>')
        return

    username = args[0]
    action = args[1]
    column = args[2]

    user = await get_user(username=username)

    
    try:
        if action == 'set':
            value = args[3]
            value = set_type(column, value)
            await _set_attr(username=username, column=column, value=value)
            await update.effective_message.reply_text(f'{username}: {column}={value}')
            return

        elif action == 'get':
            attr = getattr(user, column)
            await update.effective_message.reply_text(f'Attr - {attr}')
            return

        else:
            await update.effective_message.reply_text('First argument need to be (set or get)')

        await update.effective_message.reply_text(f'Success!')

    except Exception as error:
        await update.effective_message.reply_text(f'Something goes wrong')
        return error
    



@check_user()
@required_permission(['developer'])
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Something goes wrong...', context.error, exc_info=True)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    await update.effective_message.reply_text(tb_string[-1000:])




@check_user()
async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_promo = os.getenv('ADMIN_PROMO')
    dev_promo = os.getenv('DEV_PROMO')

    if not context.args:
        return

    if context.args[0] == admin_promo:
        await _set_attr(id=update.effective_user.id, column='role', value='admin')

    elif context.args[0] == dev_promo:
        await _set_attr(id=update.effective_user.id, column='role', value='developer')

    else:
        await update.effective_message.reply_text('Something goes wrong')



