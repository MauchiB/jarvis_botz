from telegram import LabeledPrice, Update, ShippingOption, InlineKeyboardMarkup, InlineKeyboardButton
from jarvis_botz.bot.contexttypes import CustomTypes
from telegram.ext import (
    PreCheckoutQueryHandler,
    ShippingQueryHandler, ConversationHandler


)
from jarvis_botz.utils import check_user

state_payment = 0


@check_user()
async def start_payment_1(update: Update, context: CustomTypes) -> None:
    await update.message.reply_text(
    "Пожалуйста, напишите кол-во звездочек, которые вы хотите потратить на токены (1 звезда = 10 токенов)." \
    "\n\nНапример, для покупки 5,000 токенов введите '500'."
    )

    return state_payment


@check_user()
async def start_payment_2(update: Update, context: CustomTypes) -> None:
    stars = update.message.text.strip()
    if not stars.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректное число звездочек. (Только цифры)")
        return state_payment
    
    tokens = int(stars) * 10

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Оплатить {stars} ⭐️", pay=True)]])
    
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title='💰 Покупка токенов',
        description=f"Вы покупаете {tokens} токенов для ИИ-бота.\n\n✅ Быстрое зачисление\n✅ Доступ ко всем функциям",
        payload=f'tokens_{tokens}_payload',
        provider_token='',
        currency='XTR',
        prices=[LabeledPrice(label=f'{tokens} токенов', amount=stars)],
        reply_markup=keyboard
    )

    return ConversationHandler.END



@check_user()
async def precheckout_callback(update: Update, context: CustomTypes) -> None:
    query = update.pre_checkout_query

    print(query.invoice_payload)

    if not query.invoice_payload.startswith('tokens_') or not query.invoice_payload.endswith('_payload'):
        await query.answer(ok=False, error_message="Something went wrong...")
    
    else:
        await query.answer(ok=True)


@check_user()
async def successful_payment_callback(update: Update, context: CustomTypes) -> None:
    context.user_data['last_payment_charge_id'] = update.effective_message.successful_payment.telegram_payment_charge_id

    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)
        tokens = int(update.effective_message.successful_payment.invoice_payload.split('_')[1])
        await user_repo._set_attr(id=update.effective_user.id, update_data={'tokens':tokens})

    await update.message.reply_text("Спасибо за покупку! Ваши токены были успешно зачислены.")

@check_user()
async def refund_payment_callback(update: Update, context: CustomTypes) -> None:
    if context.user_data.get('last_payment_charge_id'):
        await context.bot.refund_star_payment(
            user_id=update.effective_user.id,
            telegram_payment_charge_id=context.user_data['last_payment_charge_id']
        )
        await update.message.reply_text("Your refund has been processed.")