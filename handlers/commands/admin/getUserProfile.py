from datetime import timedelta, datetime

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, Router

from constants import DECK_MAP, SUBS_TYPE, COUPONS
from database import execute_query, execute_select_all, execute_select
from filters.baseFilters import IsAdmin
from aiogram import F, Bot

from functions.subscription.sub import give_sub
from handlers.commands.user import get_user_profile

router = Router()

logger_chat = -4668410440


class AdminStates(StatesGroup):
    waiting_meanings_amount = State()
    waiting_coupon_amount = State()
    waiting_sub_days = State()
    waiting_referrals_amount = State()
    waiting_paid_spreads_amount = State()


@router.message(IsAdmin(), F.text.lower().startswith("!п"))
async def admin_view_profile(message: types.Message, bot: Bot):
    args = message.text.split()

    user_id = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(args) > 1:
        if args[1].isdigit():
            user_id = int(args[1])
        else:
            username = args[1].lstrip('@')
            user_id_result = await execute_select("SELECT user_id FROM users WHERE username = $1", (username,))
            if user_id_result and user_id_result:
                user_id = user_id_result
            else:
                await message.reply(f"Пользователь с именем @{username} не найден.")
                return
    else:
        await message.reply("Укажите ID или имя пользователя, или ответьте на сообщение пользователя.")
        return

    await show_user_profile(message, user_id)


async def show_user_profile(message, user_id):
    user_profile = await get_user_profile(user_id)

    bonuses = await execute_select_all("SELECT paid_spreads, referrals_paid, referrals FROM users WHERE user_id = $1",
                                       (user_id,))

    paid_spread, referrals_paid, referrals = bonuses[0]

    if not user_profile or not user_profile[0]:
        await message.reply(f"Профиль пользователя с ID {user_id} не найден.")
        return

    profile_data = user_profile[0]

    deck_type = profile_data[0]
    subscription = profile_data[1]
    subscription_date = profile_data[2]
    day_follow = {
        "moon_follow": profile_data[3],
        "day_card_follow": profile_data[4],
        "week_card_follow": profile_data[5],
        "month_card_follow": profile_data[6],
    }
    interactions = profile_data[7]
    booster = profile_data[8]
    referrals_ids = profile_data[9]
    paid_meanings = profile_data[10]
    coupon_gold = profile_data[11]
    coupon_silver = profile_data[12]
    coupon_iron = profile_data[13]

    coupons = (f"{coupon_gold} золот{'ых' if coupon_gold != 1 else 'ой'}, "
               f"{coupon_silver} серебрян{'ых' if coupon_silver != 1 else 'ый'}, "
               f"{coupon_iron} железн{'ых' if coupon_iron != 1 else 'ый'}")

    deck_type = DECK_MAP[deck_type] if deck_type else "Не указано"
    subscription = SUBS_TYPE[subscription]['name'] if subscription else "Без подписки"

    subscription_date = subscription_date if subscription_date else "Без подписки"
    interactions = interactions if interactions else "Не указано"
    booster = 'Да' if booster else 'Нет'

    paid_meanings = paid_meanings if paid_meanings else "0"

    moon_follow = "Есть" if day_follow['moon_follow'] else 'Нет'
    day_card_follow = "Есть" if day_follow['day_card_follow'] else 'Нет'
    week_card_follow = "Есть" if day_follow['week_card_follow'] else 'Нет'
    month_card_follow = "Есть" if day_follow['month_card_follow'] else 'Нет'

    user_link = f'<a href="tg://user?id={user_id}">{user_id}</a>'

    profile_text = (
        f"📋 <b>Профиль пользователя</b> (ID: {user_link})\n\n"
        f"<b>Колода:</b> {deck_type}\n"
        f"<b>Подписка:</b> {subscription}\n"
        f"<b>Конец подписки:</b> {subscription_date}\n"
        f"<b>Кол-во трактовок от Ли:</b> {paid_meanings}\n"
        f"<b>Рассылки:</b>\n"
        f"    🌙 Луна: {moon_follow}\n"
        f"    🌞 Расклад дня: {day_card_follow}\n"
        f"    📅 Расклад недели: {week_card_follow}\n"
        f"    📆 Расклад месяца: {month_card_follow}\n"
        f"<b>Купоны:</b> {coupons}\n"
        f"<b>Взаимодействий:</b> {interactions}\n"
        f"<b>Буст:</b> {booster}\n"
        f"<b>Приглашенных на расклады:</b> {referrals_paid}\n"
        f"<b>Приглашенных в Ли:</b> {len(referrals)}\n"
        f"<b>Платных раскладов:</b> {paid_spread}\n"
    )

    admin_profile_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "➕ Трактовки", callback_data = f"admin_meanings_{user_id}"),
                InlineKeyboardButton(text = "💰 Купоны", callback_data = f"admin_coupons_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "🔄 Подписка", callback_data = f"admin_subscription_{user_id}"),
                InlineKeyboardButton(text = "👥 Друзья", callback_data = f"admin_referrals_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "👁 Платные расклады", callback_data = f"admin_paidspreads_{user_id}")
            ]
        ]
    )

    await message.answer(profile_text, reply_markup = admin_profile_keyboard)


@router.callback_query(lambda c: c.data.startswith("admin_meanings_"))
async def admin_meanings_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    meanings_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "+1", callback_data = f"add_meanings_{user_id}_1"),
                InlineKeyboardButton(text = "+3", callback_data = f"add_meanings_{user_id}_3"),
                InlineKeyboardButton(text = "+5", callback_data = f"add_meanings_{user_id}_5")
            ],
            [
                InlineKeyboardButton(text = "+10", callback_data = f"add_meanings_{user_id}_10"),
                InlineKeyboardButton(text = "+20", callback_data = f"add_meanings_{user_id}_20"),
                InlineKeyboardButton(text = "+50", callback_data = f"add_meanings_{user_id}_50")
            ],
            [
                InlineKeyboardButton(text = "Ввести вручную", callback_data = f"manual_meanings_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к профилю", callback_data = f"back_to_profile_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите количество трактовок для добавления пользователю (ID: {user_id}):",
        reply_markup = meanings_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("admin_coupons_"))
async def admin_coupons_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    coupons_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "Золотые", callback_data = f"coupon_type_{user_id}_gold")
            ],
            [
                InlineKeyboardButton(text = "Серебряные", callback_data = f"coupon_type_{user_id}_silver")
            ],
            [
                InlineKeyboardButton(text = "Железные", callback_data = f"coupon_type_{user_id}_iron")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к профилю", callback_data = f"back_to_profile_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите тип купонов для добавления пользователю (ID: {user_id}):",
        reply_markup = coupons_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("coupon_type_"))
async def coupon_type_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    coupon_type = parts[3]
    await callback_query.answer()
    coupon_name = COUPONS[coupon_type]["fname"]

    coupon_amount_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "+1", callback_data = f"add_coupon_{user_id}_{coupon_type}_1"),
                InlineKeyboardButton(text = "+3", callback_data = f"add_coupon_{user_id}_{coupon_type}_3"),
                InlineKeyboardButton(text = "+5", callback_data = f"add_coupon_{user_id}_{coupon_type}_5")
            ],
            [
                InlineKeyboardButton(text = "Ввести вручную", callback_data = f"manual_coupon_{user_id}_{coupon_type}")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к купонам", callback_data = f"admin_coupons_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите количество {coupon_name} купонов для добавления пользователю (ID: {user_id}):",
        reply_markup = coupon_amount_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("admin_subscription_"))
async def admin_subscription_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    subscription_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "Шут", callback_data = f"sub_type_{user_id}_1")
            ],
            [
                InlineKeyboardButton(text = "Маг", callback_data = f"sub_type_{user_id}_2")
            ],
            [
                InlineKeyboardButton(text = "Жрица", callback_data = f"sub_type_{user_id}_3")
            ],
            [
                InlineKeyboardButton(text = "Отменить подписку", callback_data = f"cancel_subscription_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к профилю", callback_data = f"back_to_profile_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите тип подписки для пользователя (ID: {user_id}):",
        reply_markup = subscription_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("sub_type_"))
async def sub_type_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    sub_type = int(parts[3])
    await callback_query.answer()

    sub_name = SUBS_TYPE[sub_type]['name']

    sub_duration_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "7 дней", callback_data = f"add_sub_{user_id}_{sub_type}_7"),
                InlineKeyboardButton(text = "14 дней", callback_data = f"add_sub_{user_id}_{sub_type}_14")
            ],
            [
                InlineKeyboardButton(text = "30 дней", callback_data = f"add_sub_{user_id}_{sub_type}_30"),
                InlineKeyboardButton(text = "90 дней", callback_data = f"add_sub_{user_id}_{sub_type}_90")
            ],
            [
                InlineKeyboardButton(text = "180 дней", callback_data = f"add_sub_{user_id}_{sub_type}_180"),
                InlineKeyboardButton(text = "365 дней", callback_data = f"add_sub_{user_id}_{sub_type}_365")
            ],
            [
                InlineKeyboardButton(text = "Ввести вручную", callback_data = f"manual_sub_{user_id}_{sub_type}")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к типам", callback_data = f"admin_subscription_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите срок {sub_name} подписки для пользователя (ID: {user_id}):",
        reply_markup = sub_duration_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("admin_referrals_"))
async def admin_referrals_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    referrals_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "+1", callback_data = f"add_referrals_{user_id}_1"),
                InlineKeyboardButton(text = "+3", callback_data = f"add_referrals_{user_id}_3"),
                InlineKeyboardButton(text = "+5", callback_data = f"add_referrals_{user_id}_5")
            ],
            [
                InlineKeyboardButton(text = "+10", callback_data = f"add_referrals_{user_id}_10"),
                InlineKeyboardButton(text = "Ввести вручную", callback_data = f"manual_referrals_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к профилю", callback_data = f"back_to_profile_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите количество друзей (реферралов) для добавления пользователю (ID: {user_id}):",
        reply_markup = referrals_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("admin_paidspreads_"))
async def admin_referrals_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    referrals_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "+1", callback_data = f"add_paidspreads_{user_id}_1"),
                InlineKeyboardButton(text = "+2", callback_data = f"add_paidspreads_{user_id}_2"),
                InlineKeyboardButton(text = "+3", callback_data = f"add_paidspreads_{user_id}_3")
            ],
            [
                InlineKeyboardButton(text = "+4", callback_data = f"add_paidspreads_{user_id}_4"),
                InlineKeyboardButton(text = "+5", callback_data = f"add_paidspreads_{user_id}_5"),
                InlineKeyboardButton(text = "+6", callback_data = f"add_paidspreads_{user_id}_6")
            ],
            [
                InlineKeyboardButton(text = "+10", callback_data = f"add_paidspreads_{user_id}_10"),
                InlineKeyboardButton(text = "Ввести вручную", callback_data = f"add_paidspreads_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "🔙 Назад к профилю", callback_data = f"back_to_profile_{user_id}")
            ]
        ]
    )

    await callback_query.message.edit_text(
        f"Выберите количество платных раскладов для добавления пользователю (ID: {user_id}):",
        reply_markup = referrals_keyboard
    )


@router.callback_query(lambda c: c.data.startswith("add_meanings_"))
async def add_meanings_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])

    await execute_query(
        "UPDATE users SET paid_meanings = paid_meanings + $1 WHERE user_id = $2",
        (amount, user_id)
    )
    await callback_query.message.edit_text(
        text = f"Добавлено {amount} трактовок пользователю с ID {user_id}!", reply_markup = None)
    await show_user_profile(callback_query.message, user_id)


@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_meanings_"))
async def manual_meanings_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    await state.set_state("waiting_meanings_amount")
    await state.update_data(user_id = user_id)

    await callback_query.message.edit_text(
        f"Введите количество трактовок для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


@router.callback_query(lambda c: c.data.startswith("add_coupon_"))
async def add_coupon_callback(callback_query: types.CallbackQuery, bot: Bot):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    coupon_type = parts[3]
    amount = int(parts[4])
    await callback_query.answer()
    await bot.send_message(logger_chat, f"Добавлено {amount} {coupon_type} купонов пользователю {user_id}!")

    column = COUPONS[coupon_type]["field"]

    await execute_query(
        f"UPDATE users SET {column} = {column} + $1 WHERE user_id = $2",
        (amount, user_id)
    )
    await callback_query.message.edit_text(text = f"Добавлено {amount} {coupon_type} купонов пользователю {user_id}!",
                                           reply_markup = None)
    await show_user_profile(callback_query.message, user_id)


@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_coupon_"))
async def manual_coupon_callback(callback_query: types.CallbackQuery, state: FSMContext):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    coupon_type = parts[3]
    await callback_query.answer()
    await state.set_state("waiting_coupon_amount")
    await state.update_data(user_id = user_id, coupon_type = coupon_type)

    coupon_name = COUPONS[coupon_type]["name"]

    await callback_query.message.edit_text(
        f"Введите количество {coupon_name} купонов для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


@router.callback_query(lambda c: c.data.startswith("add_sub_"))
async def add_subscription_callback(callback_query: types.CallbackQuery, bot: Bot):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    sub_type = int(parts[3])
    days = int(parts[4])
    await callback_query.answer()

    date = await give_sub(user_id, days, sub_type)
    await bot.send_message(logger_chat,
                           f"Установлена подписка {sub_type} на {days} дней для {user_id}! Закончится {date}")
    await callback_query.message.edit_text(
        text = f"Установлена подписка {sub_type} на {days} дней для {user_id}! Закончится {date}", reply_markup = None)
    await show_user_profile(callback_query.message, user_id)


@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_sub_"))
async def manual_sub_callback(callback_query: types.CallbackQuery, state: FSMContext):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    sub_type = parts[3]
    await callback_query.answer()
    await state.set_state("waiting_sub_days")
    await state.update_data(user_id = user_id, sub_type = sub_type)

    sub_name = SUBS_TYPE[sub_type]['name']

    await callback_query.message.edit_text(
        f"Введите количество дней для {sub_name} подписки пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


@router.callback_query(lambda c: c.data.startswith("cancel_subscription_"))
async def cancel_subscription_callback(callback_query: types.CallbackQuery, bot: Bot):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer("Подписка отменена!")
    await bot.send_message(logger_chat, f"Подписка отменена!")
    await execute_query(
        "UPDATE users SET subscription = NULL, subscription_date = NULL WHERE user_id = $1",
        (user_id,)
    )

    await show_user_profile(callback_query.message, user_id)


@router.callback_query(lambda c: c.data.startswith("add_referrals_"))
async def add_referrals_callback(callback_query: types.CallbackQuery, bot: Bot):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])

    await bot.send_message(logger_chat, f"Добавлено {amount} друзей пользователю {user_id}!")
    await execute_query(
        "UPDATE users SET referrals_paid = referrals_paid + $1 WHERE user_id = $2",
        (amount, user_id)
    )
    await callback_query.message.edit_text(text = f"Добавлено {amount} друзей пользователю {user_id}!",
                                           reply_markup = None)
    await show_user_profile(callback_query.message, user_id)


@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_referrals_"))
async def manual_referrals_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    await state.set_state("waiting_referrals_amount")
    await state.update_data(user_id = user_id)

    await callback_query.message.edit_text(
        f"Введите количество друзей для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


@router.callback_query(lambda c: c.data.startswith("add_paidspreads_"))
async def add_paid_spreads_callback(callback_query: types.CallbackQuery, bot: Bot):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])

    await bot.send_message(logger_chat, f"Добавлено {amount} друзей пользователю {user_id}!")
    await execute_query(
        "UPDATE users SET paid_spreads = paid_spreads + $1 WHERE user_id = $2",
        (amount, user_id)
    )
    await callback_query.message.edit_text(text = f"Добавлено {amount} платных раскладов пользователю {user_id}!",
                                           reply_markup = None)
    await show_user_profile(callback_query.message, user_id)


@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_paidspreads_"))
async def manual_paid_spreads_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    await state.set_state("waiting_paid_spreads_amount")
    await state.update_data(user_id = user_id)

    await callback_query.message.edit_text(
        f"Введите количество платных раскладов для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


@router.callback_query(lambda c: c.data.startswith("back_to_profile_"))
async def back_to_profile_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.message.delete()
    await callback_query.answer()
    await show_user_profile(callback_query.message, user_id)


@router.message(AdminStates.waiting_meanings_amount)
async def process_meanings_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        await execute_query(
            "UPDATE users SET paid_meanings = paid_meanings + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        await message.reply(f"Добавлено {amount} трактовок пользователю с ID {user_id}.")

        await state.clear()

        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_coupon_amount)
async def process_coupon_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    coupon_type = data.get("coupon_type")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        column = COUPONS[coupon_type]["field"]

        await execute_query(
            f"UPDATE users SET {column} = {column} + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        coupon_name = COUPONS[coupon_type]["fname"]

        await message.reply(f"Добавлено {amount} {coupon_name} купонов пользователю с ID {user_id}.")

        await state.clear()

        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_sub_days)
async def process_sub_days(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    sub_type = data.get("sub_type")

    try:
        days = int(message.text.strip())
        if days <= 0:
            await message.reply("Количество дней должно быть положительным числом.")
            return

        current_sub_data = await execute_query(
            "SELECT subscription_date FROM users WHERE user_id = $1", (user_id,)
        )

        if current_sub_data and current_sub_data[0] and current_sub_data[0][0]:
            current_date = datetime.strptime(current_sub_data[0][0], "%Y-%m-%d")
            new_date = current_date + timedelta(days = days)
        else:
            new_date = datetime.now() + timedelta(days = days)

        await execute_query(
            "UPDATE users SET subscription = $1, subscription_date = $2 WHERE user_id = $3",
            (sub_type, new_date.strftime("%Y-%m-%d"), user_id)
        )

        sub_name = SUBS_TYPE[sub_type]['name']

        await message.reply(
            f"Установлена подписка {sub_name} на {days} дней для пользователя с ID {user_id}.\n"
            f"Дата окончания: {new_date.strftime('%Y-%m-%d')}"
        )

        await state.clear()

        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_referrals_amount)
async def process_referrals_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        await execute_query(
            "UPDATE users SET referrals_paid = referrals_paid + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        await message.reply(f"Добавлено {amount} друзей пользователю с ID {user_id}.")

        await state.clear()

        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_paid_spreads_amount)
async def process_paid_spreads_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        await execute_query(
            "UPDATE users SET paid_spreads = paid_spreads + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        await message.reply(f"Добавлено {amount} платных раскладов пользователю с ID {user_id}.")

        await state.clear()

        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")
