import asyncio
import logging

from aiogram import Router, F, types, Bot
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.exceptions import TelegramAPIError

from filters.baseFilters import IsChannel
from keyboard import follow_channel_keyboard
from middlewares.subscription import check_subscription

router = Router()


async def delete_from_db(bot: Bot, user_id, channel_id):
    try:
        await asyncio.sleep(300)

        if await check_subscription(user_id, bot, channel_id):
            try:
                await bot.send_message(
                    user_id,
                    "— Спасибо, что передумали, удачного Вам дня!"
                )
            except TelegramAPIError as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        else:
            try:
                await bot.send_message(
                    user_id,
                    "— До свидания, рады были видеть тебя у нас!"
                )
                # await execute_query("DELETE FROM users WHERE user_id = $1", (user_id,))
                logging.info(f"Пользователь {user_id} удален из базы данных")
            except TelegramAPIError as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                # await execute_query("DELETE FROM users WHERE user_id = $1", (user_id,))
    except Exception as e:
        logging.error(f"Ошибка в процессе удаления из БД для пользователя {user_id}: {e}")


@router.chat_member(
    IsChannel(),
    ChatMemberUpdatedFilter(member_status_changed = IS_MEMBER >> IS_NOT_MEMBER)
)
async def left_channel_handler(chat_member: types.ChatMemberUpdated, bot: Bot, channel_id):
    user_id = chat_member.from_user.id
    try:
        await bot.send_message(
            user_id,
            "— Очень жаль, что ты вышел из канала Дыхание Леса и больше не будешь делать расклады у "
            "меня. Мне придется удалить всю информацию о тебе и твоих раскладах. "
            "У тебя есть 5 минут, чтобы вернуться и предотвратить удаление.",
            reply_markup = follow_channel_keyboard
        )
        _ = asyncio.create_task(delete_from_db(bot, user_id, channel_id))
    except TelegramAPIError as e:
        logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        # await execute_query("DELETE FROM users WHERE user_id = $1", (user_id,))
    except Exception as e:
        logging.error(f"Неожиданная ошибка при обработке выхода из канала для {user_id}: {e}")
