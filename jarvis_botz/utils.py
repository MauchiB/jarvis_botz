from jarvis_botz.bot.database import get_user

def get_attr_table(user):
    info = ''
    
    for column in user.__table__.columns:
        value = getattr(user, column.name)
        info += f'{column.name} - {value} \n'

    return info



def check_token(type:str, user):
    tokens = user.tokens
    if type == 'TEXT' and tokens >= 0.5:
            return True
    elif type == 'IMAGE' and tokens >= 10:
            return True
    else:
        False



def require_start(func):
    async def wrapper(update, context):
        if not get_user(update.effective_user.id):
            await update.effective_message.reply_text(
                "Please use /start first to initialize your account."
            )
            return
        return await func(update, context)
    return wrapper



def admin_require(func):
    async def wrapper(update, context):
        user = get_user(update.effective_user.id)
        if not user:
            return
        
        if user.role in ['admin', 'developer']:
            return await func(update, context)
        
    return wrapper