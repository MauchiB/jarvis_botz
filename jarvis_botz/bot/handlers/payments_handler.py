from enum import Enum, auto

from telegram import (
    Update,
    LabeledPrice,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ConversationHandler
)

from jarvis_botz.bot.contexttypes import CustomTypes
from jarvis_botz.utils import check_user



class PaymentState(Enum):
    WAIT_STARS = auto()


STAR_TO_TOKENS = 10
MIN_STARS = 1



@check_user()
async def start_payment(update: Update, context: CustomTypes):
    await update.message.reply_text(
        "⭐️ Введите количество звёзд, которые хотите потратить\n"
        f"1 ⭐️ = {STAR_TO_TOKENS} токенов\n\n"
        "Например: 500"
    )
    return PaymentState.WAIT_STARS




@check_user()
async def wait_stars(update: Update, context: CustomTypes):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ Нужно ввести число (только цифры).")
        return PaymentState.WAIT_STARS

    stars = int(text)

    if stars < MIN_STARS:
        await update.message.reply_text("❌ Количество должно быть больше 0.")
        return PaymentState.WAIT_STARS

    tokens = stars * STAR_TO_TOKENS

    context.user_data["payment"] = {
        "stars": stars,
        "tokens": tokens,
    }

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"💎 Оплатить {stars} ⭐️", pay=True)]]
    )

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title="💰 Покупка токенов",
        description=(
            f"Вы покупаете {tokens} токенов\n\n"
            "✅ Мгновенное зачисление\n"
            "✅ Доступ ко всем функциям"
        ),
        payload=f"tokens_{tokens}",
        provider_token="",   # ← звёзды, поэтому пусто
        currency="XTR",
        prices=[LabeledPrice(label=f"{tokens} токенов", amount=stars)],
        reply_markup=keyboard,
    )

    return ConversationHandler.END




@check_user()
async def precheckout_callback(update: Update, context: CustomTypes):
    query = update.pre_checkout_query

    if not query.invoice_payload.startswith("tokens_"):
        await query.answer(ok=False, error_message="Invalid payment payload.")
        return

    await query.answer(ok=True)




@check_user()
async def successful_payment_callback(update: Update, context: CustomTypes):
    payment = update.message.successful_payment
    tokens = int(payment.invoice_payload.split("_")[1])

    context.user_data["last_payment_charge_id"] = payment.telegram_payment_charge_id

    async with context.session_factory() as session:
        user_repo = context.user_repo(session=session)
        await user_repo._set_attr(
            id=update.effective_user.id,
            update_data={"tokens": tokens},
        )

    await update.message.reply_text(
        f"✅ Оплата успешна!\n"
        f"🎉 Вам начислено {tokens} токенов"
    )




@check_user()
async def refund_payment_callback(update: Update, context: CustomTypes):
    charge_id = context.user_data.get("last_payment_charge_id")

    if not charge_id:
        await update.message.reply_text("❌ Нет платежа для возврата.")
        return

    await context.bot.refund_star_payment(
        user_id=update.effective_user.id,
        telegram_payment_charge_id=charge_id,
    )

    await update.message.reply_text("💸 Возврат выполнен.")
