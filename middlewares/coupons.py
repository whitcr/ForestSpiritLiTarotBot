import random
from typing import Any, Awaitable, Callable, Dict
import logging
from aiogram.types import TelegramObject
from aiogram.dispatcher.event.bases import UNHANDLED

from database import execute_query

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class CouponMiddleware:
    CARD_CHANCES = {
        "золотой": {"chance": 0.001, "field": "coupon_gold", "sale": "50"},
        "серебряный": {"chance": 0.002, "field": "coupon_silver", "sale": "25"},
        "железный": {"chance": 0.003, "field": "coupon_iron", "sale": "10"},
    }

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        result = await handler(event, data)

        if result is UNHANDLED:
            return result

        random_number = random.random()
        user_id = data.get('event_from_user').id

        for card, info in self.CARD_CHANCES.items():
            if random_number <= info["chance"]:
                await self.update_coupon(user_id, info["field"])
                await self.notify_user(data, card, info["sale"])
                break

        return result

    async def update_coupon(self, user_id: int, field: str):
        await execute_query(f"UPDATE users SET {field} = {field} + 1 WHERE user_id = $1;", (user_id,))

    async def notify_user(self, data: Dict[str, Any], card: str, sale: str):
        user = data.get('event_from_user')
        bot = data.get('bot')
        chat = data.get('event_chat')

        logger.info(f"{card} купон выдали пользователю {user.id}, ник: {user.username}, имя: {user.full_name}")

        await bot.send_message(chat.id,
                               f" @{user.username if user.username else user.full_name}, Вам выдали {card} купон! "
                               f"Он дает скидку {sale}% на личные расклады.")
