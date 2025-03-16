import logging
from typing import List, Union, Optional

from aiogram import Bot, Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from database import execute_query, execute_select, execute_select_all

router = Router()

CHANNEL_IDS = ["@forestspirito"]


async def init_db():
    await execute_query("""
    CREATE TABLE IF NOT EXISTS contest_users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        ticket_number INT,
        referrer_id BIGINT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """, ())

    await execute_query("""
    CREATE TABLE IF NOT EXISTS contest_settings (
        id SERIAL PRIMARY KEY,
        is_active BOOLEAN DEFAULT TRUE,
        prize_description TEXT,
        referral_prize_description TEXT,
        min_referrals INT DEFAULT 3,
        winners_count INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ends_at TIMESTAMP
    )
    """, ())

    await execute_query("""
    CREATE TABLE IF NOT EXISTS contest_messages (
        id SERIAL PRIMARY KEY,
        message_text TEXT,
        file_id TEXT,
        file_type TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """, ())

    settings = await execute_select("SELECT id FROM contest_settings LIMIT 1")
    if not settings:
        await execute_query("""
        INSERT INTO contest_settings (prize_description, referral_prize_description, min_referrals, winners_count)
        VALUES ($1,$2, $3, $4)
        """, ("Exciting prizes await the winners!", "Special gift for inviting friends!", 3, 1))


async def check_subscription(user_id: int, bot) -> bool:
    try:
        for channel_id in CHANNEL_IDS:
            try:
                member = await bot.get_chat_member(chat_id = channel_id, user_id = user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    return False
            except TelegramBadRequest:
                logging.error(f"Failed to check subscription for channel {channel_id}")
                return False
        return True
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False


async def get_user_ticket(user_id: int) -> Union[int, None]:
    result = await execute_select("SELECT ticket_number FROM contest_users WHERE user_id = $1", (user_id,))
    return result if result else None


async def register_user(user_id: int, username: str, first_name: str, referrer_id: Optional[int] = None) -> int:
    existing = await execute_select("SELECT ticket_number FROM contest_users WHERE user_id = $1", (user_id,))
    if existing:
        return existing[0]

    last_ticket = await execute_select("SELECT MAX(ticket_number) FROM contest_users")
    next_ticket = 1 if not last_ticket or last_ticket[0] is None else last_ticket[0] + 1

    await execute_query(
        "INSERT INTO contest_users (user_id, username, first_name, ticket_number, referrer_id) VALUES ($1,$2, $3, $4, $5)",
        (user_id, username, first_name, next_ticket, referrer_id)
    )

    if referrer_id:
        logging.info(f"User {user_id} was referred by {referrer_id}")

    return next_ticket


async def get_referral_link(user_id: int, bot) -> str:
    return f"https://t.me/{(await bot.get_me()).username}?start=contest{user_id}"


async def get_referrals(user_id: int, bot) -> List[dict]:
    results = await execute_select_all(
        """
        SELECT u.user_id, u.username, u.first_name 
        FROM contest_users u 
        WHERE u.referrer_id = $1
        """,
        (user_id,)
    )

    referrals = []
    for row in results:
        is_subscribed = await check_subscription(row[0], bot)
        referrals.append({
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "is_subscribed": is_subscribed
        })

    return referrals


async def get_valid_referrals_count(user_id: int, bot) -> int:
    referrals = await get_referrals(user_id, bot)
    return sum(1 for ref in referrals if ref["is_subscribed"])


async def is_eligible_for_referral_prize(user_id: int, bot) -> bool:
    settings = await execute_select("SELECT min_referrals FROM contest_settings ORDER BY id DESC LIMIT 1")
    min_referrals = settings if settings else 3

    valid_count = await get_valid_referrals_count(user_id, bot)
    return valid_count >= min_referrals


async def generate_ticket_image(ticket_number: int) -> FSInputFile:
    return FSInputFile("contest_ticket.png")


# Keyboards
def get_subscription_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for channel_id in CHANNEL_IDS:
        channel_name = channel_id.replace("@", "")
        builder.add(InlineKeyboardButton(text = f"Подписаться на {channel_name}", url = f"https://t.me/{channel_name}"))

    builder.add(InlineKeyboardButton(text = "✅ Проверить подписки", callback_data = "check_subscriptions"))

    builder.adjust(1)
    return builder.as_markup()


def get_contest_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text = "📝 Мой билет", callback_data = "my_ticket"))
    builder.add(InlineKeyboardButton(text = "👥 Пригласить друзей", callback_data = "invite_friends"))
    builder.add(InlineKeyboardButton(text = "👨‍👩‍👧‍👦 Мои приглашённые", callback_data = "my_referrals"))
    builder.add(InlineKeyboardButton(text = "🎁 Мои призы", callback_data = "my_prizes"))

    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("contest", "конкурс"))
async def contest_command(message: types.Message):
    user_id = message.from_user.id
    await init_db()
    contest_active = await execute_select("SELECT is_active FROM contest_settings ORDER BY id DESC LIMIT 1")
    if not contest_active:
        await message.answer("В данный момент конкурс не проводится. Следите за анонсами!")
        return

    ticket = await get_user_ticket(user_id)

    if ticket:
        await message.answer(
            "Вы уже участвуете в конкурсе! Ваш номер билета: " + str(ticket),
            reply_markup = get_contest_menu_keyboard(user_id)
        )
    else:
        await message.answer(
            "Для участия в конкурсе подпишитесь на следующие каналы и нажмите кнопку проверки:",
            reply_markup = get_subscription_keyboard()
        )


@router.callback_query(F.data == "check_subscriptions")
async def check_subscriptions_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    is_subscribed = await check_subscription(user_id, bot)

    if is_subscribed:
        ticket_number = await register_user(
            user_id = user_id,
            username = callback.from_user.username,
            first_name = callback.from_user.first_name
        )

        contest_info = await execute_select(
            "SELECT prize_description FROM contest_settings ORDER BY id DESC LIMIT 1"
        )
        prize_description = contest_info if contest_info else "Exciting prizes await the winners!"

        try:
            await callback.message.answer(f"🎫 Ваш номер билета: {ticket_number}")

            await callback.message.answer(
                f"🎉 Поздравляем! Вы официально участвуете в конкурсе!\n\n"
                f"🏆 Призы конкурса:\n{prize_description}\n\n"
                f"Используйте меню ниже для управления вашим участием:",
                reply_markup = get_contest_menu_keyboard(user_id)
            )

            await callback.answer("Вы успешно зарегистрированы в конкурсе!")
        except Exception as e:
            logging.error(f"Error sending ticket: {e}")
            await callback.message.answer(
                "Произошла ошибка при генерации билета. Пожалуйста, попробуйте позже или обратитесь к администратору."
            )
            await callback.answer("Ошибка при генерации билета")
    else:
        await callback.answer("Вы не подписались на все каналы! Проверьте подписки и попробуйте снова.",
                              show_alert = True)


@router.callback_query(F.data == "my_ticket")
async def my_ticket_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ticket_number = await get_user_ticket(user_id)

    if ticket_number:
        await callback.message.answer(f"🎫 Ваш билет участника конкурса:\nНомер: {ticket_number}")
        await callback.answer("Ваш билет")
    else:
        await callback.message.answer(
            "Вы не участвуете в конкурсе. Используйте команду /contest для регистрации.",
            reply_markup = get_subscription_keyboard()
        )
        await callback.answer("Вы не участвуете в конкурсе")


@router.callback_query(F.data == "invite_friends")
async def invite_friends_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    ticket_number = await get_user_ticket(user_id)

    if not ticket_number:
        await callback.message.answer(
            "Вы не участвуете в конкурсе. Используйте команду /contest для регистрации.",
            reply_markup = get_subscription_keyboard()
        )
        await callback.answer("Вы не участвуете в конкурсе")
        return

    settings = await execute_select_all(
        "SELECT referral_prize_description, min_referrals FROM contest_settings ORDER BY id DESC LIMIT 1"
    )

    if settings:
        ref_prize, min_refs = settings[0]
    else:
        ref_prize = "Special gift for inviting friends!"
        min_refs = 3

    ref_link = await get_referral_link(user_id, bot)

    await callback.message.answer(
        f"🔗 Ваша реферальная ссылка для приглашения друзей:\n\n"
        f"{ref_link}\n\n"
        f"👥 Пригласите {min_refs} друзей, которые также подпишутся на все каналы, "
        f"и получите специальный приз:\n\n"
        f"🎁 {ref_prize}"
    )
    await callback.answer("Ваша реферальная ссылка")


@router.callback_query(F.data == "my_referrals")
async def my_referrals_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    ticket_number = await get_user_ticket(user_id)

    if not ticket_number:
        await callback.message.answer(
            "Вы не участвуете в конкурсе. Используйте команду /contest для регистрации.",
            reply_markup = get_subscription_keyboard()
        )
        await callback.answer("Вы не участвуете в конкурсе")
        return

    referrals = await get_referrals(user_id, bot)
    valid_referrals = [r for r in referrals if r["is_subscribed"]]

    settings = await execute_select("SELECT min_referrals FROM contest_settings ORDER BY id DESC LIMIT 1")
    min_referrals = settings if settings else 3

    if not referrals:
        await callback.message.answer(
            "Вы еще никого не пригласили. Используйте пункт 'Пригласить друзей' чтобы получить реферальную ссылку."
        )
        await callback.answer("У вас нет приглашенных")
        return

    ref_list = ""
    for i, ref in enumerate(referrals, 1):
        status = "✅" if ref["is_subscribed"] else "❌"
        username = f"@{ref['username']}" if ref["username"] else ref["first_name"]
        ref_list += f"{i}. {username} - {status}\n"

    progress = f"{len(valid_referrals)}/{min_referrals}"
    eligible = len(valid_referrals) >= min_referrals

    await callback.message.answer(
        f"👥 Ваши приглашенные друзья ({progress}):\n\n"
        f"{ref_list}\n"
        f"{'🎊 Поздравляем! Вы достигли необходимого количества рефералов и получаете приз!' if eligible else 'Пригласите еще друзей для получения приза.'}"
    )
    await callback.answer("Список приглашенных")


@router.callback_query(F.data == "my_prizes")
async def my_prizes_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    ticket_number = await get_user_ticket(user_id)

    if not ticket_number:
        await callback.message.answer(
            "Вы не участвуете в конкурсе. Используйте команду /contest для регистрации.",
            reply_markup = get_subscription_keyboard()
        )
        await callback.answer("Вы не участвуете в конкурсе")
        return

    is_eligible = await is_eligible_for_referral_prize(user_id, bot)

    if is_eligible:
        settings = await execute_select(
            "SELECT referral_prize_description FROM contest_settings ORDER BY id DESC LIMIT 1")
        ref_prize = settings if settings else "Special gift for inviting friends!"

        await callback.message.answer(
            f"🎁 Ваши призы:\n\n"
            f"1. Реферальный приз: {ref_prize}\n\n"
            f"Чтобы получить приз, свяжитесь с администратором."
        )
    else:
        await callback.message.answer(
            "У вас пока нет призов. Продолжайте участвовать в конкурсе, чтобы выиграть!"
        )

    await callback.answer("Информация о призах")


async def contest_with_referral(message: types.Message):
    deep_link = message.text.split()[1] if len(message.text.split()) > 1 else ""
    user_id = message.from_user.id

    try:
        referrer_id = int(deep_link.replace("contest", ""))

        referrer_ticket = await get_user_ticket(referrer_id)

        if referrer_ticket:
            user_ticket = await get_user_ticket(user_id)

            if user_ticket:
                await message.answer(
                    "Вы уже участвуете в конкурсе! Используйте команду /contest для просмотра информации.",
                    reply_markup = get_contest_menu_keyboard(user_id)
                )
            else:
                contest_active = await execute_select(
                    "SELECT is_active FROM contest_settings ORDER BY id DESC LIMIT 1")
                if not contest_active or not contest_active[0]:
                    await message.answer("В данный момент конкурс не проводится. Следите за анонсами!")
                    return

                await message.answer(
                    f"Вас пригласил участник конкурса!\n\n"
                    f"Для участия подпишитесь на следующие каналы и нажмите кнопку проверки:",
                    reply_markup = get_subscription_keyboard()
                )

                await execute_query(
                    "INSERT INTO contest_users (user_id, username, first_name, referrer_id, ticket_number) VALUES ($1,$2, $3, $4, $5) "
                    "ON CONFLICT (user_id) DO UPDATE SET referrer_id = EXCLUDED.referrer_id",
                    (user_id, message.from_user.username, message.from_user.first_name, referrer_id, None)
                )
        else:
            await message.answer(
                "Неверная реферальная ссылка. Используйте команду /contest для участия в конкурсе."
            )
    except Exception as e:
        logging.error(f"Error processing referral: {e}")
        await message.answer(
            "Произошла ошибка при обработке реферальной ссылки. Используйте команду /contest для участия в конкурсе."
        )
    else:
        await message.answer(
            "Добро пожаловать! Используйте команду /contest для участия в конкурсе."
        )
