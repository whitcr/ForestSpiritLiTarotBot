from aiogram import Router, types, Bot
from aiogram.exceptions import TelegramForbiddenError

from database import execute_query, execute_select
from filters.baseFilters import IsChannel

router = Router()


@router.chat_boost(IsChannel())
async def chat_boost_handler(chat_boost: types.ChatBoostUpdated, channel_id, bot: Bot):
    if chat_boost.chat.id == channel_id:
        user_id = chat_boost.boost.source.user.id

        title = chat_boost.chat.title
        username_channel = chat_boost.chat.username

        user_exists = await execute_select("SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)", (user_id,))
        if not user_exists:
            await execute_query("INSERT INTO users (user_id, boosted) VALUES ($1, $2)", (user_id, 0))

        current_value = await execute_select("SELECT boosted FROM users WHERE user_id = $1", (user_id,))
        new_value = int(current_value) + 1
        await execute_query("UPDATE users SET boosted = $1 WHERE user_id = $2", (new_value, user_id))

        message = f"Спасибо, что дали буст каналу {title} (@{username_channel})."
        try:
            await bot.send_message(user_id, message)
        except TelegramForbiddenError:
            pass


@router.removed_chat_boost(IsChannel())
async def removed_chat_boost_handler(removed_chat_boost: types.ChatBoostRemoved, channel_id, bot: Bot):
    if removed_chat_boost.chat.id == channel_id:
        user_id = removed_chat_boost.source.user.id

        title = removed_chat_boost.chat.title
        username_channel = removed_chat_boost.chat.username

        current_value = await execute_select("SELECT boosted FROM users WHERE user_id = $1", (user_id,))
        new_value = int(current_value) - 1
        await execute_query("UPDATE users SET boosted = $1 WHERE user_id = $2", (new_value, user_id))

        if new_value == 0:
            message = f"К сожалению, вы забрали все бусты с канала {title} (@{username_channel})."
            try:
                await bot.send_message(user_id, message)
            except TelegramForbiddenError:
                pass
