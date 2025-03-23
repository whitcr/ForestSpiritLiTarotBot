from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter

from constants import SUBS_TYPE
from database import execute_select
from keyboard import sub_keyboard


class SubscriptionLevel(BaseFilter):
    def __init__(self, required_level: int, use_meanings: bool = False):
        self.required_level = required_level
        self.use_meanings = use_meanings

    async def __call__(self, event: Message | CallbackQuery, bot: Bot) -> bool:
        user_id = event.from_user.id
        sub = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))

        use_meanings = False
        if self.use_meanings:
            result = await execute_select("SELECT paid_meanings FROM users WHERE user_id = $1", (user_id,))
            use_meanings = result >= 1 if result else False

        if sub >= self.required_level or use_meanings:
            return True
        else:
            required_sub = SUBS_TYPE[self.required_level]['name']

            await bot.send_message(user_id,
                                   f"У вас нет доступа к этой функции, но вы можете приобрести ее по подписке {required_sub}",
                                   reply_markup = sub_keyboard
                                   )
            return False


async def get_subscription(user_id, subscription):
    result = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))
    return result >= int(subscription)
