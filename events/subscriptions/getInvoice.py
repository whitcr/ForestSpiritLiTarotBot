from aiogram import Router, F, types, Bot
from aiogram.types import LabeledPrice, FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from constants import SUBS_TYPE, DURATION_DISCOUNTS, PAID_MEANINGS_COST
from functions.subscription.sub import give_sub, give_meanings

router = Router()
LOGGER_CHAT = -4668410440


class SubscriptionCallback(CallbackData, prefix = "get_sub"):
    sub: int
    duration: int
    amount: int


class MeaningsCallback(CallbackData, prefix = "get_meanings"):
    count: int
    amount: int


async def get_sub_type_keyboard():
    sub_keyboard = InlineKeyboardBuilder()
    for i in range(1, 4):
        sub_keyboard.button(
            text = SUBS_TYPE[i]["name"],
            callback_data = f"select_sub_type_{i}"
        )

    sub_keyboard.button(
        text = "💰 Tрактовки",
        callback_data = f"select_meanings_type",
        row_width = 1
    )
    sub_keyboard.button(
        text = "◀️ Назад в профиль",
        callback_data = "get_my_profile",
        row_width = 1)
    sub_keyboard.adjust(3)
    return sub_keyboard


def calculate_discounted_price(base_price, duration):
    discount_percent = DURATION_DISCOUNTS[duration]
    discount_multiplier = (100 - discount_percent) / 100
    return int(base_price * duration * discount_multiplier)


def format_duration(duration):
    if duration == 1:
        return f"{duration} месяц"
    elif 2 <= duration <= 4:
        return f"{duration} месяца"
    else:
        return f"{duration} месяцев"


@router.callback_query(F.data.startswith("get_sub_menu"))
async def process_subscription(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    text = 'Типы подписок:\n\n'
    for i in range(1, 4):
        text += f"{SUBS_TYPE[i]['name']} — {SUBS_TYPE[i]['stars']} звезд/{SUBS_TYPE[i]['euros']} евро/{SUBS_TYPE[i]['rubles']} рублей за месяц\n\n"

    text += (
        "Выберите тип подписки или трактовки для покупки. \n\nВы также можете приобрести дополнительные платные трактовки, если вам не хватает:")

    sub_keyboard = await get_sub_type_keyboard()

    photo = InputMediaPhoto(media = FSInputFile(f'images/tech/subs/base.png'))

    try:
        await bot.edit_message_media(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            media = photo
        )
        await bot.edit_message_caption(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            caption = text,
            reply_markup = sub_keyboard.as_markup()
        )
    except Exception:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_photo(
            chat_id = call.message.chat.id,
            photo = FSInputFile(f'images/tech/subs/base.png'),
            caption = text,
            reply_markup = sub_keyboard.as_markup()
        )


@router.callback_query(F.data.startswith("select_sub_type_"))
async def process_select_duration(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    sub_type = int(call.data.split("_")[-1])

    duration_keyboard = InlineKeyboardBuilder()

    text = f'Выберите длительность подписки "{SUBS_TYPE[sub_type]["name"]}":\n\n'

    for duration in DURATION_DISCOUNTS.keys():
        original_stars = SUBS_TYPE[sub_type]["stars"] * duration
        discounted_stars = calculate_discounted_price(SUBS_TYPE[sub_type]["stars"], duration)

        original_rubles = SUBS_TYPE[sub_type]["rubles"] * duration
        discounted_rubles = calculate_discounted_price(SUBS_TYPE[sub_type]["rubles"], duration)

        original_euros = SUBS_TYPE[sub_type]["euros"] * duration
        discounted_euros = calculate_discounted_price(SUBS_TYPE[sub_type]["euros"], duration)

        discount_text = f" (-{DURATION_DISCOUNTS[duration]}%)" if DURATION_DISCOUNTS[duration] > 0 else ""

        duration_word = 'месяц' if duration == 1 else 'месяца' if duration <= 4 else 'месяцев'

        text += f"<b>{duration} {duration_word}{discount_text}:</b>\n"

        if DURATION_DISCOUNTS[duration] > 0:
            text += f"• <b>{discounted_stars}</b> Stars вместо {original_stars} Stars\n"
        else:
            text += f"• <b>{discounted_stars}</b> Stars\n"

        if DURATION_DISCOUNTS[duration] > 0:
            text += f"• <b>{discounted_rubles}</b> ₽ вместо {original_rubles} ₽\n"
        else:
            text += f"• <b>{discounted_rubles}</b> ₽\n"

        if DURATION_DISCOUNTS[duration] > 0:
            text += f"• <b>{discounted_euros:.2f}</b> € вместо {original_euros:.2f} €\n"
        else:
            text += f"• <b>{discounted_euros:.2f}</b> €\n"

        text += "\n"

        button_text = f"{duration} {duration_word} {discount_text}"
        duration_keyboard.button(
            text = button_text,
            callback_data = SubscriptionCallback(
                sub = sub_type,
                duration = duration,
                amount = discounted_stars
            ).pack()
        )

    duration_keyboard.button(
        text = "← Назад к выбору типа",
        callback_data = "get_sub_menu"
    )

    duration_keyboard.adjust(1)

    photo = InputMediaPhoto(media = FSInputFile(f'images/tech/subs/{sub_type}.png'))

    try:
        await bot.edit_message_media(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            media = photo
        )
        await bot.edit_message_caption(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            caption = text,
            reply_markup = duration_keyboard.as_markup(),
            parse_mode = "HTML"
        )
    except Exception:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_photo(
            chat_id = call.message.chat.id,
            photo = FSInputFile(f'images/tech/subs/{sub_type}.png'),
            caption = text,
            reply_markup = duration_keyboard.as_markup(),
            parse_mode = "HTML"
        )


@router.callback_query(SubscriptionCallback.filter())
async def process_buy_command(call: types.CallbackQuery, callback_data: SubscriptionCallback, bot: Bot):
    await call.answer()

    sub_type = callback_data.sub
    duration = callback_data.duration
    amount = callback_data.amount

    name = SUBS_TYPE[sub_type]['name']
    duration_text = f"{duration} {'месяц' if duration == 1 else 'месяца' if duration <= 4 else 'месяцев'}"
    discount_text = f" (скидка {DURATION_DISCOUNTS[duration]}%)" if DURATION_DISCOUNTS[duration] > 0 else ""

    price = [LabeledPrice(label = f'Подписка {name} на {duration_text}{discount_text}', amount = amount)]

    payment_keyboard = InlineKeyboardBuilder()
    payment_keyboard.button(text = f"{amount} Telegram Stars", pay = True)
    payment_keyboard.button(text = f"Boosty (рубли/евро)", callback_data = f"boosty_payment_{sub_type}_{duration}")
    payment_keyboard.button(text = "Соглашение", callback_data = "get_privacy")
    payment_keyboard.adjust(1)

    await bot.send_invoice(
        call.message.chat.id,
        title = 'Премиум подписка на Ли',
        description = f"Подписка — {name} на {duration_text}{discount_text}",
        provider_token = '',
        currency = 'XTR',
        is_flexible = False,
        prices = price,
        payload = f"sub_{sub_type}_{duration}",
        reply_markup = payment_keyboard.as_markup()
    )


@router.callback_query(F.data.startswith("select_meanings_type"))
async def process_select_meanings(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    meanings_keyboard = InlineKeyboardBuilder()

    text = f'Выберите количество трактовок:\n\n'

    for count, price_info in PAID_MEANINGS_COST.items():
        stars = price_info["stars"]
        rubles = price_info["rubles"]
        euros = price_info["euros"]
        sale = price_info["sale"]

        if sale > 0:
            discounted_stars = int(stars * (100 - sale) / 100)
            discounted_rubles = int(rubles * (100 - sale) / 100)
            discounted_euros = euros * (100 - sale) / 100

            sale_text = f" (-{sale}%)"

            text += f"<b>{count} трактовок{sale_text}:</b>\n"
            text += f"• <b>{discounted_stars}</b> Stars вместо {stars} Stars\n"
            text += f"• <b>{discounted_rubles}</b> ₽ вместо {rubles} ₽\n"
            text += f"• <b>{discounted_euros:.2f}</b> € вместо {euros:.2f} €\n"

            callback_data = MeaningsCallback(
                count = count,
                amount = discounted_stars
            ).pack()

            button_text = f"{count} трактовок{sale_text}"
        else:
            text += f"<b>{count} трактовок:</b>\n"
            text += f"• <b>{stars}</b> Stars\n"
            text += f"• <b>{rubles}</b> ₽\n"
            text += f"• <b>{euros:.2f}</b> €\n"

            callback_data = MeaningsCallback(
                count = count,
                amount = stars
            ).pack()

            button_text = f"{count} трактовок"

        text += "\n"

        meanings_keyboard.button(
            text = button_text,
            callback_data = callback_data
        )

    meanings_keyboard.button(
        text = "← Назад к главному меню",
        callback_data = "get_sub_menu"
    )

    meanings_keyboard.adjust(1)

    try:
        await bot.edit_message_caption(
            chat_id = call.message.chat.id,
            message_id = call.message.message_id,
            caption = text,
            reply_markup = meanings_keyboard.as_markup(),
            parse_mode = "HTML"
        )
    except Exception:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(
            chat_id = call.message.chat.id,
            text = text,
            reply_markup = meanings_keyboard.as_markup(),
            parse_mode = "HTML"
        )


@router.callback_query(MeaningsCallback.filter())
async def process_buy_meanings(call: types.CallbackQuery, callback_data: MeaningsCallback, bot: Bot):
    await call.answer()

    count = callback_data.count
    amount = callback_data.amount

    sale = PAID_MEANINGS_COST[count]["sale"]
    sale_text = f" (скидка {sale}%)" if sale > 0 else ""

    price = [LabeledPrice(label = f'{count} трактовок{sale_text}', amount = amount)]

    payment_keyboard = InlineKeyboardBuilder()
    payment_keyboard.button(text = f"{amount} Telegram Stars", pay = True)
    payment_keyboard.button(text = f"Boosty (рубли/евро)", callback_data = f"boosty_payment_meanings_{count}")
    payment_keyboard.button(text = "Соглашение", callback_data = "get_privacy")
    payment_keyboard.adjust(1)

    await bot.send_invoice(
        call.message.chat.id,
        title = 'Покупка трактовок',
        description = f"{count} индивидуальных трактовок{sale_text}",
        provider_token = '',
        currency = 'XTR',
        is_flexible = False,
        prices = price,
        payload = f"meanings_{count}",
        reply_markup = payment_keyboard.as_markup()
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    await bot.send_message(LOGGER_CHAT,
                           f"Pre-checkout query received from user {pre_checkout_query.from_user.id} ({pre_checkout_query.from_user.full_name}).")
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok = True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    payload_parts = payload.split("_")
    payment_type = payload_parts[0]

    await bot.send_message(
        LOGGER_CHAT,
        f"Payment successful for user {user_id} ({message.from_user.full_name}): "
        f"Type: {payment_type}, "
        f"Amount: {message.successful_payment.total_amount} {message.successful_payment.currency}. "
        f"Details: {message.successful_payment}."
    )
    sub_type = int(payload_parts[1])
    duration_months = int(payload_parts[2])
    if payment_type == "sub":

        date = await give_sub(user_id, duration_months * 30, str(sub_type))

        sub_name = SUBS_TYPE[sub_type]['name']
        duration_text = format_duration(duration_months)

        await bot.send_message(
            LOGGER_CHAT,
            f"Subscription activated for user {user_id}: "
            f"Type {sub_name} for {duration_text}, "
            f"Expires on {date}."
        )

        success_text = (f'Ваш платеж принят! Спасибо за приобретение подписки {sub_name} на {duration_text} за '
                        f'{message.successful_payment.total_amount} {message.successful_payment.currency}. '
                        f'Ваша подписка закончится {date}.')

    elif payment_type == "meanings":
        meanings_count = int(payload_parts[1])

        await give_meanings(user_id, meanings_count)

        await bot.send_message(
            LOGGER_CHAT,
            f"Added {meanings_count} meanings for user {user_id}."
        )

        success_text = (f'Ваш платеж принят! Спасибо за приобретение {meanings_count} трактовок за '
                        f'{message.successful_payment.total_amount} {message.successful_payment.currency}. '
                        f'Трактовки добавлены к вашему аккаунту.')

    else:
        success_text = f'Ваш платеж принят! Спасибо за покупку.'

    await bot.send_message(
        chat_id = message.chat.id,
        text = success_text
    )

    await bot.delete_message(message.chat.id, message.message_id)
    return
