from aiogram import F, Router, Bot
from aiogram.filters.chat_member_updated import\
    ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.types import ChatMemberUpdated
from aiogram.exceptions import TelegramAPIError
import logging

from database import execute_query

router = Router()
router.my_chat_member.filter(F.chat.type == "private")
router.message.filter(F.chat.type == "private")


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed = MEMBER >> KICKED)
)
async def user_blocked_bot(event: ChatMemberUpdated):
    try:
        await execute_query("DELETE FROM users WHERE user_id = $1", (event.from_user.id,))
        logging.info(f"Пользователь {event.from_user.id} заблокировал бота и удален из базы данных")
    except Exception as e:
        logging.error(f"Ошибка при удалении пользователя {event.from_user.id} из базы: {e}")


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed = KICKED >> MEMBER)
)
async def user_unblocked_bot(event: ChatMemberUpdated, bot: Bot):
    try:
        await bot.send_message(
            event.from_user.id,
            "Привет, рад, что ты меня разблокировал. В бане было очень грустно :( "
        )
        logging.info(f"Пользователь {event.from_user.id} разблокировал бота")
    except TelegramAPIError as e:
        logging.error(f"Не удалось отправить сообщение пользователю {event.from_user.id}: {e}")
