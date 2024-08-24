from aiogram.types import Message
from aiogram.filters import BaseFilter

from constants import SUBS_TYPE
from database import execute_select


class SubscriptionLevel(BaseFilter):
    def __init__(self, required_level: int):
        self.required_level = required_level

    async def __call__(self, message: Message) -> bool:
        sub = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (message.from_user.id,))

        if sub >= self.required_level:
            return True
        else:
            required_sub = SUBS_TYPE[self.required_level]
            await message.answer(
                f"У вас нет доступа к этой функции, но вы можете приобрести ее по подписке {required_sub}",
                reply_to_message_id = message.message_id
            )
            return False


async def get_subscription(user_id, subscription):
    result = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))
    return result == subscription
