from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import execute_select, execute_query
from keyboard import follow_channel_keyboard
from middlewares.subscription import check_subscription

router = Router()


@router.callback_query(F.data == 'get_referral_url')
async def process_callback_get_referral_url(callback_query: CallbackQuery, bot: Bot, channel_id):
    await callback_query.answer()
    user_id = callback_query.from_user.id

    referrals_ids = await execute_select("SELECT referrals FROM users WHERE user_id = $1", (user_id,))

    referral_link = f'https://t.me/ForestSpiritLi_bot?start=ref_{user_id}'
    text = f'Ваша ссылка для приглашения друзей:\n\n<code>{referral_link}</code>\n\n'

    if referrals_ids:
        if len(referrals_ids) >= 1:
            count, removed = await get_referral_count(user_id, bot, channel_id)
            referrals = await get_names_from_array_ids(referrals_ids, bot)

            text += f"Твои приглашенные: {referrals}"

            if len(removed) > 0:
                removed = await get_names_from_array_ids(removed, bot)
                text += f"\nИз них не подписаны на канал: {removed}"
    else:
        text += "Нет приглашенных"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text = "◀️ Назад в профиль", callback_data = "get_my_profile")
    keyboard.adjust(1)

    await bot.edit_message_text(
        chat_id = callback_query.message.chat.id,
        message_id = callback_query.message.message_id,
        text = text,
        reply_markup = keyboard.as_markup()
    )


async def get_referral_count(user_id, bot, channel_id):
    invited_result = await execute_select("SELECT referrals FROM users WHERE user_id = $1", (user_id,))

    if invited_result is False:
        return 0, []

    count = 0
    removed = []
    for user in invited_result:
        if await check_subscription(user, bot, channel_id):
            count += 1
        else:
            removed.append(user)

    return count, removed


async def get_referral_count_text(user_id, bot, channel_id):
    count, removed = await get_referral_count(user_id, bot, channel_id)
    removed = await get_names_from_array_ids(removed, bot)
    text = f"Количество приглашенных и подписанных на канал - {count}, не подписаны: {removed}"
    return text


async def get_referrals(bot, message, command_params):
    referrer_id = int(command_params.split("_")[-1])
    user_id = message.from_user.id

    if user_id == referrer_id:
        await bot.send_message(user_id, f"Пригласил сам себя? Умно, но.. нет!")
        return

    check = await execute_select("SELECT user_id FROM users WHERE user_id = $1", (user_id,))
    invited = await execute_select("SELECT referrals FROM users WHERE user_id = $1", (referrer_id,))
    invited = invited if invited else []

    if user_id not in invited:
        invited.append(user_id)
        await execute_query("UPDATE users SET referrals = $1 WHERE user_id = $2", (invited, referrer_id))
        await bot.send_message(referrer_id,
                               f"Ты пригласил друга, спасибо!")
        await bot.send_message(user_id,
                               'Тебя пригласил друг, рады видеть, чтобы приглашение было засчитано - подпишитесь на '
                               'наш канал :)', reply_markup = follow_channel_keyboard)
    elif check is False:
        await bot.send_message(referrer_id,
                               f"Друг, которого ты пригласил, уже есть в канале.")
        await bot.send_message(user_id,
                               'Ты уже состоишь в канале, приглашения не засчитано.')
    return


async def get_names_from_array_ids(array, bot):
    results = []
    for user_id in array:
        try:
            user = await bot.get_chat(user_id)
            if user.first_name:
                results.append(f"@{user.username}")  # Ник
            elif user.username:
                results.append(f'<a href="tg://user?id={user_id}">{user.first_name}</a>')  # Имя
            else:
                results.append(f'<a href="tg://user?id={user_id}">{user_id}</a>')  # Кликабельный ID
        except Exception as e:
            results.append(f"Ошибка: {e}")

    return ", ".join(results)
