from aiogram import Dispatcher, BaseMiddleware, Router, exceptions
import keyboard as kb
from constants import ADMIN_ID, CHANNEL_ID, CHANNEL
from functions.statistics import get_statistic_users, delete_message
from main import dp, bot
from typing import Any, Callable, Dict, Awaitable
from aiogram.types import Message, CallbackQuery, TelegramObject


class CheckingSubscription(BaseMiddleware):
    def check_subscription(user_id):
        try:
            chat_member = bot.get_chat_member(chat_id = CHANNEL_ID, user_id = user_id)
            return chat_member.status in {types.ChatMemberStatus.MEMBER, types.ChatMemberStatus.CREATOR,
                                          types.ChatMemberStatus.ADMINISTRATOR}
        except exceptions.TelegramAPIError:
            return False

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        if self.check_subscription(event.from_user.id):
            return await handler(event, data)

        msg = await message.reply(
            text = 'Вы должны быть подключены к моему информационному полю, чтобы я мог вам помогать.',
            reply_markup = kb.follow_channel_keyboard)
        await delete_message(msg, 30)
        return
