import random
from typing import Any, Awaitable, Callable, Dict
import logging
from aiogram.types import TelegramObject
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.utils.markdown import hlink

from constants import COUPONS
from database import execute_query

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

logger_chat = -4739443638


class CouponMiddleware:

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        result = await handler(event, data)

        if result is UNHANDLED:
            return result

        try:
            random_number = random.random()
            user_id = data.get('event_from_user').id

            for card, info in COUPONS.items():
                if random_number <= info["chance"]:
                    await self.update_coupon(user_id, info["field"])
                    await self.notify_user(data, info["name"], info["sale"])
                    break

            return result

        except:
            pass

    async def update_coupon(self, user_id: int, field: str):
        await execute_query(f"UPDATE users SET {field} = {field} + 1 WHERE user_id = $1;", (user_id,))

    async def notify_user(self, data: Dict[str, Any], card: str, sale: str):
        user = data.get('event_from_user')
        bot = data.get('bot')
        chat = data.get('event_chat')

        user_link = f"tg://user?id={user.id}"
        await bot.send_message(
            logger_chat,
            f"✅ Выдал {card} купон!\n\n"
            f"Пользователь {hlink(f'{user.id}', user_link)}."
        )

        logger.info(f"{card} купон выдали пользователю {user.id}, ник: {user.username}, имя: {user.full_name}")

        await bot.send_message(chat.id,
                               f" @{user.username if user.username else user.full_name}, Вам выдали {card} купон! "
                               f"Он дает скидку {sale}% на личные расклады.")
