import logging
import datetime
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import SUBS_TYPE, DURATION_DISCOUNTS, PAID_MEANINGS_COST
from events.subscriptions.getInvoice import calculate_discounted_price, format_duration
from functions.subscription.sub import give_sub, give_meanings

LOGGER_CHAT = -4668410440
router = Router()


class PaymentScreenshot(StatesGroup):
    waiting_for_screenshot = State()
    payment_details = State()


@router.callback_query(F.data.startswith("boosty_payment_"))
async def boosty_payment(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()

    parts = call.data.split("_")
    payment_type = parts[2]

    if payment_type == "meanings":
        meanings_count = int(parts[3])

        price_info = PAID_MEANINGS_COST[meanings_count]
        base_price = price_info['rubles']
        sale = price_info['sale']
        discounted_price = int(base_price * (100 - sale) / 100) if sale > 0 else base_price

        discount_text = f" (скидка {sale}%)" if sale > 0 else ""

        await state.update_data(payment_type = "meanings", meanings_count = meanings_count)

        boosty_keyboard = InlineKeyboardBuilder()
        boosty_keyboard.button(text = f"💳 Оплатить {discounted_price}₽", url = "https://boosty.to/forestspirit/donate")
        boosty_keyboard.button(text = "📸 Отправить скрин", callback_data = "send_payment_screenshot")
        boosty_keyboard.adjust(1)

        await bot.send_message(
            chat_id = call.message.chat.id,
            text = f"Для оплаты {meanings_count} трактовок{discount_text} через Boosty:\n\n"
                   f"1. Нажмите на кнопку 'Оплатить {discounted_price}₽'\n"
                   f"2. Введите сумму доната {discounted_price} рублей\n"
                   f"3. Оплатите и сделайте скриншот подтверждения\n"
                   f"4. Нажмите 'Отправить скрин' и загрузите изображение"
                   f"\n\nВ течении 6 часов оплата будет проверена, а трактовки будут добавлены на ваш аккаунт.",
            reply_markup = boosty_keyboard.as_markup()
        )
    else:
        sub_type = int(payment_type)
        duration = int(parts[3]) if len(parts) > 3 else 1

        base_price = SUBS_TYPE[sub_type]['rubles']
        discounted_price = calculate_discounted_price(base_price, duration)

        name = SUBS_TYPE[sub_type]['name']
        duration_text = format_duration(duration)
        discount_text = f" (скидка {DURATION_DISCOUNTS[duration]}%)" if DURATION_DISCOUNTS[duration] > 0 else ""

        await state.update_data(payment_type = "subscription", sub_type = sub_type, duration = duration)

        boosty_keyboard = InlineKeyboardBuilder()
        boosty_keyboard.button(text = f"💳 Оплатить {discounted_price}₽", url = "https://boosty.to/forestspirit/donate")
        boosty_keyboard.button(text = "📸 Отправить скрин", callback_data = "send_payment_screenshot")
        boosty_keyboard.adjust(1)

        await bot.send_message(
            chat_id = call.message.chat.id,
            text = f"Для оплаты подписки {name} на {duration_text}{discount_text} через Boosty:\n\n"
                   f"1. Нажмите на кнопку 'Оплатить {discounted_price}₽'\n"
                   f"2. Введите сумму доната {discounted_price} рублей\n"
                   f"3. Оплатите и сделайте скриншот подтверждения\n"
                   f"4. Нажмите 'Отправить скрин' и загрузите изображение"
                   f"\n\nВ течении 6 часов оплата будет проверена, а подписка будет активирована.",
            reply_markup = boosty_keyboard.as_markup()
        )


@router.callback_query(F.data == "send_payment_screenshot")
async def ask_for_screenshot(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📸 Пожалуйста, отправьте фото скриншота оплаты.")
    await state.set_state(PaymentScreenshot.waiting_for_screenshot)


@router.message(PaymentScreenshot.waiting_for_screenshot, F.photo)
async def process_screenshot(message: types.Message, bot: Bot, state: FSMContext):
    try:
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else f"[ID: {user_id}](tg://user?id={user_id})"
        photo_id = message.photo[-1].file_id

        state_data = await state.get_data()
        payment_type = state_data.get("payment_type", "subscription")

        keyboard = InlineKeyboardBuilder()
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        if payment_type == "subscription":
            sub_type = state_data.get("sub_type", 1)
            duration = state_data.get("duration", 1)

            requested_sub_name = SUBS_TYPE[sub_type]['name']
            duration_text = format_duration(duration)
            discount_text = f" (скидка {DURATION_DISCOUNTS[duration]}%)" if DURATION_DISCOUNTS[duration] > 0 else ""

            base_price = SUBS_TYPE[sub_type]['rubles']
            discounted_price = calculate_discounted_price(base_price, duration)

            keyboard.button(
                text = "✅ Принять оплату",
                callback_data = f"approve_sub:{sub_type}:{duration}:{user_id}"
            )
            keyboard.button(
                text = "❌ Отклонить",
                callback_data = f"reject_payment:{user_id}"
            )
            keyboard.adjust(1)

            caption = (
                f"📩 <b>Новая заявка на подписку</b>\n"
                f"⏱ Время заявки: {current_time}\n"
                f"👤 Пользователь: {username}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"📊 Подписка: <b>{requested_sub_name}</b>\n"
                f"⏱ Длительность: <b>{duration_text}</b>{discount_text}\n"
                f"💰 Сумма: <b>{discounted_price}₽</b>\n\n"
                f"Статус: ⏳ Ожидает проверки"
            )

        else:  # payment_type == "meanings"
            # Обработка скриншота для трактовок
            meanings_count = state_data.get("meanings_count", 10)

            price_info = PAID_MEANINGS_COST[meanings_count]
            base_price = price_info['rubles']
            sale = price_info['sale']
            discounted_price = int(base_price * (100 - sale) / 100) if sale > 0 else base_price
            discount_text = f" (скидка {sale}%)" if sale > 0 else ""

            keyboard.button(
                text = "✅ Принять оплату",
                callback_data = f"approve_meanings:{meanings_count}:{user_id}"
            )
            keyboard.button(
                text = "❌ Отклонить",
                callback_data = f"reject_payment:{user_id}"
            )
            keyboard.adjust(1)

            caption = (
                f"📩 <b>Новая заявка на покупку трактовок</b>\n"
                f"⏱ Время заявки: {current_time}\n"
                f"👤 Пользователь: {username}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"📊 Количество: <b>{meanings_count} трактовок</b>{discount_text}\n"
                f"💰 Сумма: <b>{discounted_price}₽</b>\n\n"
                f"Статус: ⏳ Ожидает проверки"
            )

        await bot.send_photo(
            chat_id = LOGGER_CHAT,
            photo = photo_id,
            caption = caption,
            reply_markup = keyboard.as_markup()
        )

        await message.answer("✅ Ваш скриншот отправлен на проверку. Ожидайте ответа.")
        await state.clear()

    except Exception as e:
        logging.error(f"Ошибка при обработке скриншота: {e}")
        await message.answer("⚠ Произошла ошибка. Попробуйте ещё раз.")


@router.message(PaymentScreenshot.waiting_for_screenshot)
async def wrong_screenshot_type(message: types.Message, state: FSMContext):
    await message.answer(
        "⚠ Пожалуйста, отправьте фото, а не текст. Нажмите кнопку '📸 Отправить скрин' и попробуйте снова.")
    await state.clear()


@router.callback_query(F.data.startswith("approve_sub:"))
async def approve_subscription(call: types.CallbackQuery, bot: Bot):
    try:
        await call.answer()

        _, sub_type, duration, user_id = call.data.split(":")
        sub_type = int(sub_type)
        duration = int(duration)
        user_id = int(user_id)

        sub_name = SUBS_TYPE[sub_type]['name']
        duration_text = format_duration(duration)

        expiry_date = await give_sub(user_id, duration * 30, sub_type)

        approval_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        await bot.send_message(
            user_id,
            f"🎉 Ваша оплата подтверждена!\n\n"
            f"Вам выдана подписка: <b>{sub_name}</b> на {duration_text}!\n"
            f"Подписка действует до {expiry_date}.\n\n"
            f"Спасибо за поддержку! ❤️"
        )

        original_caption = call.message.caption
        caption_without_status = original_caption.split("\n\nСтатус:")[0]

        admin_info = f"{call.from_user.full_name} ({call.from_user.id})" if call.from_user else "Администратор"

        new_caption = (
            f"{caption_without_status}\n\n"
            f"Статус: ✅ <b>ПОДТВЕРЖДЕНО</b>\n"
            f"Время: {approval_time}\n"
            f"Администратор: {admin_info}\n"
            f"Выдана подписка: {sub_name} на {duration_text}\n"
            f"Действует до: {expiry_date}"
        )

        await call.message.edit_caption(caption = new_caption, reply_markup = None)

    except Exception as e:
        logging.error(f"Ошибка при выдаче подписки: {e}")
        await call.message.answer(f"⚠ Произошла ошибка при выдаче подписки: {e}")


@router.callback_query(F.data.startswith("approve_meanings:"))
async def approve_meanings(call: types.CallbackQuery, bot: Bot):
    try:
        await call.answer()

        _, meanings_count, user_id = call.data.split(":")
        meanings_count = int(meanings_count)
        user_id = int(user_id)

        await give_meanings(user_id, meanings_count)

        approval_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        await bot.send_message(
            user_id,
            f"🎉 Ваша оплата подтверждена!\n\n"
            f"На ваш аккаунт добавлено: <b>{meanings_count} трактовок</b>!\n\n"
            f"Спасибо за поддержку! ❤️"
        )

        original_caption = call.message.caption
        caption_without_status = original_caption.split("\n\nСтатус:")[0]

        admin_info = f"{call.from_user.full_name} ({call.from_user.id})" if call.from_user else "Администратор"

        new_caption = (
            f"{caption_without_status}\n\n"
            f"Статус: ✅ <b>ПОДТВЕРЖДЕНО</b>\n"
            f"Время: {approval_time}\n"
            f"Администратор: {admin_info}\n"
            f"Выдано: {meanings_count} трактовок"
        )

        await call.message.edit_caption(caption = new_caption, reply_markup = None)

    except Exception as e:
        logging.error(f"Ошибка при выдаче трактовок: {e}")
        await call.message.answer(f"⚠ Произошла ошибка при выдаче трактовок: {e}")


@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment(call: types.CallbackQuery, bot: Bot):
    try:
        await call.answer()

        _, user_id = call.data.split(":")
        user_id = int(user_id)

        reject_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        await bot.send_message(
            user_id,
            "🚫 Ваш платеж не подтвержден. Возможные причины:\n"
            "- Неверная сумма платежа\n"
            "- Нечитаемый скриншот\n"
            "- Отсутствие подтверждения транзакции\n\n"
            "Пожалуйста, попробуйте снова или свяжитесь с поддержкой."
        )

        original_caption = call.message.caption
        caption_without_status = original_caption.split("\n\nСтатус:")[0]

        admin_info = f"{call.from_user.full_name} ({call.from_user.id})" if call.from_user else "Администратор"

        new_caption = (
            f"{caption_without_status}\n\n"
            f"Статус: ❌ <b>ОТКЛОНЕНО</b>\n"
            f"Время: {reject_time}\n"
            f"Администратор: {admin_info}"
        )

        await call.message.edit_caption(caption = new_caption, reply_markup = None)

    except Exception as e:
        logging.error(f"Ошибка при отклонении оплаты: {e}")
        await call.message.answer(f"⚠ Произошла ошибка при отклонении платежа: {e}")
