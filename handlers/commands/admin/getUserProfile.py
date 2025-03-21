from datetime import timedelta, datetime

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, Router

from constants import DECK_MAP, SUBS_TYPE
from database import execute_query, execute_select_all
from filters.baseFilters import IsAdmin
from aiogram import F, Bot

from handlers.commands.user import get_user_profile

router = Router()


# Определение состояний для FSM (Finite State Machine)
class AdminStates(StatesGroup):
    waiting_meanings_amount = State()
    waiting_coupon_amount = State()
    waiting_sub_days = State()
    waiting_referrals_amount = State()


@router.message(IsAdmin(), F.text.lower().startswith("!профиль"))
async def admin_view_profile(message: types.Message, bot: Bot):
    """Просмотр профиля пользователя администратором по ID, юзернейму или пересланному сообщению"""

    args = message.text.split()

    # Получаем ID пользователя
    user_id = None

    # Проверяем, есть ли пересланное сообщение
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    # Если команда содержит аргумент (ID или username)
    elif len(args) > 1:
        # Проверяем, является ли аргумент числом (ID)
        if args[1].isdigit():
            user_id = int(args[1])
        # Иначе считаем, что это username
        else:
            username = args[1].lstrip('@')
            # Здесь нужно получить ID по username
            user_id_result = await execute_query("SELECT user_id FROM users WHERE username = $1", (username,))
            if user_id_result and user_id_result[0]:
                user_id = user_id_result[0][0]
            else:
                await message.reply(f"Пользователь с именем @{username} не найден.")
                return
    else:
        await message.reply("Укажите ID или имя пользователя, или ответьте на сообщение пользователя.")
        return

    await show_user_profile(message, user_id)


async def show_user_profile(message, user_id):
    """Отображение профиля пользователя с админской клавиатурой"""
    # Получаем профиль пользователя
    user_profile = await get_user_profile(user_id)

    bonuses = await execute_select_all("SELECT paid_spread, referrals_paid, referrals FROM users WHERE user_id = $1",
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
    subscription = SUBS_TYPE[subscription] if subscription else "Без подписки"

    subscription_date = subscription_date if subscription_date else "Без подписки"
    interactions = interactions if interactions else "Не указано"
    booster = 'Да' if booster else 'Нет'

    paid_meanings = paid_meanings if paid_meanings else "0"

    # Проверка на наличие значений для day_follow и установка текстов по умолчанию
    moon_follow = "Есть" if day_follow['moon_follow'] else 'Нет'
    day_card_follow = "Есть" if day_follow['day_card_follow'] else 'Нет'
    week_card_follow = "Есть" if day_follow['week_card_follow'] else 'Нет'
    month_card_follow = "Есть" if day_follow['month_card_follow'] else 'Нет'

    # Формирование текста профиля для админа с дополнительной информацией
    profile_text = (
        f"📋 <b>Профиль пользователя</b> (ID: {user_id})\n\n"
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

    # Создаем основную админскую клавиатуру
    admin_profile_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "➕ Трактовки", callback_data = f"admin_meanings_{user_id}"),
                InlineKeyboardButton(text = "💰 Купоны", callback_data = f"admin_coupons_{user_id}")
            ],
            [
                InlineKeyboardButton(text = "🔄 Подписка", callback_data = f"admin_subscription_{user_id}"),
                InlineKeyboardButton(text = "👥 Друзья", callback_data = f"admin_referrals_{user_id}")
            ]
        ]
    )

    await message.answer(profile_text, reply_markup = admin_profile_keyboard)


# Обработчики для кнопок из админской клавиатуры

# Обработчик для трактовок
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


# Обработчик для купонов
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


# Обработчик для типов купонов
@router.callback_query(lambda c: c.data.startswith("coupon_type_"))
async def coupon_type_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    coupon_type = parts[3]
    await callback_query.answer()
    # Определяем название типа купона для отображения
    coupon_name = {
        "gold": "золотых",
        "silver": "серебряных",
        "iron": "железных"
    }.get(coupon_type, "")

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


# Обработчик для подписки
@router.callback_query(lambda c: c.data.startswith("admin_subscription_"))
async def admin_subscription_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    subscription_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "Базовая", callback_data = f"sub_type_{user_id}_1")
            ],
            [
                InlineKeyboardButton(text = "Продвинутая", callback_data = f"sub_type_{user_id}_2")
            ],
            [
                InlineKeyboardButton(text = "Премиум", callback_data = f"sub_type_{user_id}_3")
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


# Обработчик для выбора типа подписки
@router.callback_query(lambda c: c.data.startswith("sub_type_"))
async def sub_type_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    sub_type = parts[3]
    await callback_query.answer()
    # Определяем название типа подписки для отображения
    sub_name = {
        "1": "базовой",
        "2": "продвинутой",
        "3": "премиум"
    }.get(sub_type, "")

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


# Обработчик для друзей (реферралов)
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


# Обработчики для добавления трактовок
@router.callback_query(lambda c: c.data.startswith("add_meanings_"))
async def add_meanings_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])
    await callback_query.answer(f"Добавлено {amount} трактовок пользователю!")
    # Добавляем трактовки пользователю
    await execute_query(
        "UPDATE users SET paid_meanings = paid_meanings + $1 WHERE user_id = $2",
        (amount, user_id)
    )

    # Возвращаемся к профилю пользователя для отображения обновленных данных
    await show_user_profile(callback_query.message, user_id)


# Обработчик для ручного ввода количества трактовок
@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_meanings_"))
async def manual_meanings_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    # Устанавливаем состояние для ожидания ввода
    await state.set_state("waiting_meanings_amount")
    await state.update_data(user_id = user_id)

    await callback_query.message.edit_text(
        f"Введите количество трактовок для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


# Обработчик для добавления купонов
@router.callback_query(lambda c: c.data.startswith("add_coupon_"))
async def add_coupon_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    coupon_type = parts[3]
    amount = int(parts[4])
    await callback_query.answer(f"Добавлено {amount} {coupon_name} купонов пользователю!")
    # Определяем колонку в БД в зависимости от типа купона
    column = {
        "gold": "coupon_gold",
        "silver": "coupon_silver",
        "iron": "coupon_iron"
    }.get(coupon_type)

    # Добавляем купоны пользователю
    await execute_query(
        f"UPDATE users SET {column} = {column} + $1 WHERE user_id = $2",
        (amount, user_id)
    )

    coupon_name = {
        "gold": "золотых",
        "silver": "серебряных",
        "iron": "железных"
    }.get(coupon_type, "")

    # Возвращаемся к профилю пользователя для отображения обновленных данных
    await show_user_profile(callback_query.message, user_id)


# Обработчик для ручного ввода количества купонов
@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_coupon_"))
async def manual_coupon_callback(callback_query: types.CallbackQuery, state: FSMContext):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    coupon_type = parts[3]
    await callback_query.answer()
    # Устанавливаем состояние для ожидания ввода
    await state.set_state("waiting_coupon_amount")
    await state.update_data(user_id = user_id, coupon_type = coupon_type)

    coupon_name = {
        "gold": "золотых",
        "silver": "серебряных",
        "iron": "железных"
    }.get(coupon_type, "")

    await callback_query.message.edit_text(
        f"Введите количество {coupon_name} купонов для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


# Обработчик для добавления подписки
@router.callback_query(lambda c: c.data.startswith("add_sub_"))
async def add_subscription_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    sub_type = parts[3]
    days = int(parts[4])
    await callback_query.answer(f"Установлена подписка {sub_name} на {days} дней!")
    # Получаем текущую дату окончания подписки
    current_sub_data = await execute_query(
        "SELECT subscription_date FROM users WHERE user_id = $1", (user_id,)
    )

    if current_sub_data and current_sub_data[0] and current_sub_data[0][0]:
        # Если подписка уже есть, продлеваем её
        current_date = datetime.strptime(current_sub_data[0][0], "%Y-%m-%d")
        new_date = current_date + timedelta(days = days)
    else:
        # Если подписки нет, устанавливаем новую
        new_date = datetime.now() + timedelta(days = days)

    # Обновляем подписку в базе данных
    await execute_query(
        "UPDATE users SET subscription = $1, subscription_date = $2 WHERE user_id = $3",
        (sub_type, new_date.strftime("%Y-%m-%d"), user_id)
    )

    sub_name = {
        "1": "Базовая",
        "2": "Продвинутая",
        "3": "Премиум"
    }.get(sub_type, "")

    # Возвращаемся к профилю пользователя для отображения обновленных данных
    await show_user_profile(callback_query.message, user_id)


# Обработчик для ручного ввода срока подписки
@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_sub_"))
async def manual_sub_callback(callback_query: types.CallbackQuery, state: FSMContext):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    sub_type = parts[3]
    await callback_query.answer()
    # Устанавливаем состояние для ожидания ввода
    await state.set_state("waiting_sub_days")
    await state.update_data(user_id = user_id, sub_type = sub_type)

    sub_name = {
        "1": "базовой",
        "2": "продвинутой",
        "3": "премиум"
    }.get(sub_type, "")

    await callback_query.message.edit_text(
        f"Введите количество дней для {sub_name} подписки пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


# Обработчик для отмены подписки
@router.callback_query(lambda c: c.data.startswith("cancel_subscription_"))
async def cancel_subscription_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer("Подписка отменена!")
    # Обнуляем подписку в базе данных
    await execute_query(
        "UPDATE users SET subscription = NULL, subscription_date = NULL WHERE user_id = $1",
        (user_id,)
    )

    # Возвращаемся к профилю пользователя для отображения обновленных данных
    await show_user_profile(callback_query.message, user_id)


# Обработчик для добавления реферралов
@router.callback_query(lambda c: c.data.startswith("add_referrals_"))
async def add_referrals_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])
    await callback_query.answer(f"Добавлено {amount} друзей пользователю!")
    # Добавляем реферралов пользователю
    await execute_query(
        "UPDATE users SET referrals_paid = referrals_paid + $1 WHERE user_id = $2",
        (amount, user_id)
    )

    # Возвращаемся к профилю пользователя для отображения обновленных данных
    await show_user_profile(callback_query.message, user_id)


# Обработчик для ручного ввода количества реферралов
@router.callback_query(StateFilter(None), lambda c: c.data.startswith("manual_referrals_"))
async def manual_referrals_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    # Устанавливаем состояние для ожидания ввода
    await state.set_state("waiting_referrals_amount")
    await state.update_data(user_id = user_id)

    await callback_query.message.edit_text(
        f"Введите количество друзей для добавления пользователю (ID: {user_id}):\n"
        f"Отправьте число в следующем сообщении."
    )


# Обработчик для возврата к профилю
@router.callback_query(lambda c: c.data.startswith("back_to_profile_"))
async def back_to_profile_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[-1])
    await callback_query.message.delete()
    await callback_query.answer()
    # Возвращаемся к профилю пользователя
    await show_user_profile(callback_query.message, user_id)


# Обработчики текстовых сообщений для ручного ввода значений
@router.message(AdminStates.waiting_meanings_amount)
async def process_meanings_amount(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        # Добавляем трактовки пользователю
        await execute_query(
            "UPDATE users SET paid_meanings = paid_meanings + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        await message.reply(f"Добавлено {amount} трактовок пользователю с ID {user_id}.")

        # Очищаем состояние
        await state.clear()

        # Показываем обновленный профиль
        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_coupon_amount)
async def process_coupon_amount(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    user_id = data.get("user_id")
    coupon_type = data.get("coupon_type")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        # Определяем колонку в БД в зависимости от типа купона
        column = {
            "gold": "coupon_gold",
            "silver": "coupon_silver",
            "iron": "coupon_iron"
        }.get(coupon_type)

        # Добавляем купоны пользователю
        await execute_query(
            f"UPDATE users SET {column} = {column} + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        coupon_name = {
            "gold": "золотых",
            "silver": "серебряных",
            "iron": "железных"
        }.get(coupon_type, "")

        await message.reply(f"Добавлено {amount} {coupon_name} купонов пользователю с ID {user_id}.")

        # Очищаем состояние
        await state.clear()

        # Показываем обновленный профиль
        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_sub_days)
async def process_sub_days(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    user_id = data.get("user_id")
    sub_type = data.get("sub_type")

    try:
        days = int(message.text.strip())
        if days <= 0:
            await message.reply("Количество дней должно быть положительным числом.")
            return

        # Получаем текущую дату окончания подписки
        current_sub_data = await execute_query(
            "SELECT subscription_date FROM users WHERE user_id = $1", (user_id,)
        )

        if current_sub_data and current_sub_data[0] and current_sub_data[0][0]:
            # Если подписка уже есть, продлеваем её
            current_date = datetime.strptime(current_sub_data[0][0], "%Y-%m-%d")
            new_date = current_date + timedelta(days = days)
        else:
            # Если подписки нет, устанавливаем новую
            new_date = datetime.now() + timedelta(days = days)

        # Обновляем подписку в базе данных
        await execute_query(
            "UPDATE users SET subscription = $1, subscription_date = $2 WHERE user_id = $3",
            (sub_type, new_date.strftime("%Y-%m-%d"), user_id)
        )

        sub_name = {
            "1": "Шут",
            "2": "Маг",
            "3": "Жрица"
        }.get(sub_type, "")

        await message.reply(
            f"Установлена подписка {sub_name} на {days} дней для пользователя с ID {user_id}.\n"
            f"Дата окончания: {new_date.strftime('%Y-%m-%d')}"
        )

        # Очищаем состояние
        await state.clear()

        # Показываем обновленный профиль
        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(AdminStates.waiting_referrals_amount)
async def process_referrals_amount(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.reply("Количество должно быть положительным числом.")
            return

        # Добавляем реферралов пользователю
        await execute_query(
            "UPDATE users SET referrals_paid = referrals_paid + $1 WHERE user_id = $2",
            (amount, user_id)
        )

        await message.reply(f"Добавлено {amount} друзей пользователю с ID {user_id}.")

        # Очищаем состояние
        await state.clear()

        # Показываем обновленный профиль
        await show_user_profile(message, user_id)

    except ValueError:
        await message.reply("Введите корректное число.")
