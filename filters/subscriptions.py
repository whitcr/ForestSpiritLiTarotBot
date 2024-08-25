from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter

from constants import SUBS_TYPE
from database import execute_select
from functions.messages.messages import get_chat_id
from keyboard import sub_keyboard


class SubscriptionLevel(BaseFilter):
    def __init__(self, required_level: int):
        self.required_level = required_level

    async def __call__(self, event: Message | CallbackQuery, bot: Bot) -> bool:
        user_id = event.from_user.id
        sub = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))

        if sub >= self.required_level:
            return True
        else:
            required_sub = SUBS_TYPE[self.required_level]
            chat_id = await get_chat_id(event)

            await bot.send_message(user_id,
                                   f"У вас нет доступа к этой функции, но вы можете приобрести ее по подписке {required_sub}",
                                   reply_markup = sub_keyboard
                                   )
            return False


async def get_subscription(user_id, subscription):
    result = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))
    return result == subscription
