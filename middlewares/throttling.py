from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from cachetools import TTLCache

from main import bot

CACHE = TTLCache(maxsize = 10_000, ttl = 1)  # Максимальный размер кэша - 10000 ключей, а время жизни ключа - 5 секунд


class ThrottlingMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        user: User = data.get('event_from_user')

        if user.id in CACHE:
            await bot.send_message(user.id, 'Не флудите!')
            return

        CACHE[user.id] = True

        return await handler(event, data)
