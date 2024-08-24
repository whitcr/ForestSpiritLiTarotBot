from aiogram import BaseMiddleware, Bot, exceptions
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable, Dict

from functions.messages.messages import delete_message
from keyboard import follow_channel_keyboard


async def check_subscription(user_id: int, bot: Bot, channel_id: int) -> bool:
    try:
        chat_member = await bot.get_chat_member(chat_id = channel_id, user_id = user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except exceptions.TelegramAPIError:
        return False


class CheckingSubscription(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        user = data.get('event_from_user')
        chat = data.get('event_chat')
        bot = data['bot']
        channel_id = data['channel_id']

        if await check_subscription(user.id, bot, channel_id):
            return await handler(event, data)

        msg = await bot.send_message(
            chat_id = chat.id,
            text = 'Вы должны быть подключены к моему информационному каналу, чтобы я мог вам помогать.',
            reply_markup = follow_channel_keyboard
        )

        if chat == channel_id:
            return await handler(event, data)

        await delete_message(msg, 30)
        return
