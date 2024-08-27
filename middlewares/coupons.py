import random
from typing import Any, Awaitable, Callable, Dict
import logging
from aiogram.types import TelegramObject
from aiogram.dispatcher.event.bases import UNHANDLED

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class CouponMiddleware:
    GOLD_CARD_CHANCE = 0.01
    SILVER_CARD_CHANCE = 0.02
    IRON_CARD_CHANCE = 0.03

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

        if random_number <= self.GOLD_CARD_CHANCE:
            card = "золотую"
        elif random_number <= self.SILVER_CARD_CHANCE:
            card = "серебряную"
        elif random_number <= self.IRON_CARD_CHANCE:
            card = "железную"
        else:
            return result

        user = data.get('event_from_user')
        bot = data.get('bot')
        chat = data.get('event_chat')

        logging.info(
            f"{card} карта была выдана пользователю {user.id}, ник: {user.username}, имя: {user.full_name}")

        await bot.send_message(chat.id,
                               f" @{user.username if user.username else user.full_name}, Вам выдана {card} карта!")

        return result
