import datetime
import pytz
import logging
from aiogram import Router, F, types, Bot
from aiogram.types import LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from constants import SUBS_TYPE
from database import execute_query

# Configure logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


class SubscriptionCallback(CallbackData, prefix = "get_sub"):
    sub: int
    amount: int


sub_keyboard = InlineKeyboardBuilder()
sub_keyboard.button(text = "Шут", callback_data = SubscriptionCallback(sub = 1, amount = 75))
sub_keyboard.button(text = "Маг", callback_data = SubscriptionCallback(sub = 2, amount = 150))
sub_keyboard.button(text = "Жрица", callback_data = SubscriptionCallback(sub = 3, amount = 250))


@router.callback_query(F.data.startswith("get_sub_menu"))
async def process_subscription(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    logger.info(
        f"User {call.from_user.id} ({call.message.from_user.full_name}) requested subscription options.")
    await bot.send_message(chat_id = call.message.chat.id,
                           text =
                           "Типы подписок\n\n"
                           "Шут - 150 рублей (75 звезд)\n\n"
                           "Маг - 280 рублей (150 звезд)\n\n"
                           "Жрица - 450 рублей (250 звезд)",
                           reply_markup = sub_keyboard.as_markup()
                           )


@router.callback_query(SubscriptionCallback.filter())
async def process_buy_command(call: types.CallbackQuery, callback_data: SubscriptionCallback, bot: Bot):
    await call.answer()

    name = SUBS_TYPE.get(callback_data.sub, None)
    price = [LabeledPrice(label = f'Купить подписку {name}', amount = callback_data.amount)]

    logger.info(
        f"User {call.from_user.id} ({call.from_user.full_name}) selected subscription '{name}' for {callback_data.amount}.")

    await bot.send_invoice(
        call.message.chat.id,
        title = 'Премиум подписка на Ли',
        description = f"Подписка - {name}",
        provider_token = '',
        currency = 'XTR',
        is_flexible = False,
        prices = price,
        payload = str(callback_data.sub),
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    logger.info(
        f"Pre-checkout query received from user {pre_checkout_query.from_user.id} ({pre_checkout_query.from_user.full_name}).")
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok = True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message, bot: Bot):
    new_date = datetime.datetime.now(pytz.timezone('Europe/Kiev')) + datetime.timedelta(days = 30)
    date = new_date.strftime("%d.%m")

    user_id = message.from_user.id
    sub = message.successful_payment.invoice_payload

    await execute_query("update users set subscription = $1 where user_id = $2", (sub, user_id,))
    await execute_query("update users set subscription_date = $1 where user_id = $2", (date, user_id,))

    if sub == 1:
        await execute_query("update users set paid_meanings = paid_meanings + 100 where user_id = $1", (user_id,))
    elif sub == 2:
        await execute_query("update users set paid_meanings = paid_meanings + 200 where user_id = $1", (user_id,))
    elif sub == 3:
        await execute_query("update users set paid_meanings = paid_meanings + 300 where user_id = $1", (user_id,))

    sub_name = SUBS_TYPE.get(sub, None)

    logger.info(
        f"Payment successful for user {user_id} ({message.from_user.full_name}): Subscription {sub_name}, amount {message.successful_payment.total_amount} {message.successful_payment.currency}.")

    await bot.send_message(
        message.chat.id,
        f'Ваш платеж принят! Спасибо за приобретение подписки {sub_name} за '
        f'{message.successful_payment.total_amount} {message.successful_payment.currency}'
        f'Ваша подписка закончится {date}.',
    )
