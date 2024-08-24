from aiogram import Router, types, Bot
from database import execute_query
from filters.baseFilters import IsChannel

router = Router()


@router.chat_boost(IsChannel())
async def chat_boost_handler(chat_boost: types.ChatBoostUpdated, channel_id, bot: Bot):
    if chat_boost.chat.id == channel_id:
        user_id = chat_boost.boost.source.user.id

        title = chat_boost.chat.title
        username_channel = chat_boost.chat.username

        current_value = await execute_query("SELECT boosted FROM users WHERE user_id = $1", (user_id,))
        new_value = current_value[0] + 1
        await execute_query("UPDATE users SET boosted = $1 WHERE user_id = $2", (new_value, user_id))

        message = f"Спасибо, что дали буст каналу {title} (@{username_channel})."
        await bot.send_message(user_id, message)


@router.removed_chat_boost(IsChannel())
async def removed_chat_boost_handler(removed_chat_boost: types.ChatBoostRemoved, channel_id, bot: Bot):
    if removed_chat_boost.chat.id == channel_id:
        user_id = removed_chat_boost.source.user.id

        title = removed_chat_boost.chat.title
        username_channel = removed_chat_boost.chat.username

        current_value = await execute_query("SELECT boosted FROM users WHERE user_id = $1", (user_id,))
        new_value = current_value[0] - 1
        await execute_query("UPDATE users SET boosted = $1 WHERE user_id = $2", (new_value, user_id))
        
        if new_value == 0:
            message = f"К сожалению, вы забрали все бусты с канала {title} (@{username_channel})."
            await bot.send_message(user_id, message)
