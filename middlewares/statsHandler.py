from datetime import timedelta, datetime
from collections import defaultdict
import asyncio
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database import execute_query, execute_select_all


class StatisticsCache:
    def __init__(self, flush_interval: int = 60):
        self.cache = defaultdict(lambda: {
            'daily_count': 0,
            'weekly_count': 0,
            'monthly_count': 0,
            'total_count': 0
        })
        self.flush_interval = flush_interval
        self.last_flush = datetime.utcnow()
        self._lock = asyncio.Lock()
        self._flush_task = None  # Инициализируем переменную для фоновой задачи

    async def start_auto_flush(self):
        """Запускает авто-флаш в фоне, если ещё не запущено."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self.auto_flush())

    async def increment(self, command: str):
        async with self._lock:
            counts = self.cache[command]
            counts['daily_count'] += 1
            counts['weekly_count'] += 1
            counts['monthly_count'] += 1
            counts['total_count'] += 1

    async def auto_flush(self):
        """Периодически сбрасывает данные в БД."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()

    async def flush(self):
        async with self._lock:
            if not self.cache:
                return

            now = datetime.utcnow()
            today = now.date()
            week_start = today - timedelta(days = today.weekday())
            month_start = today.replace(day = 1)

            for command, counts in list(self.cache.items()):
                result = await execute_select_all(
                    """
                    SELECT daily_count, weekly_count, monthly_count, total_count,
                           last_daily_update, last_weekly_update, last_monthly_update
                    FROM statistics_handler 
                    WHERE command = $1
                    """,
                    (command,),
                )

                if result:
                    record = result[0]
                    counts['daily_count'] = counts['daily_count'] + record['daily_count']
                    counts['weekly_count'] = counts['weekly_count'] + record['weekly_count']
                    counts['monthly_count'] = counts['monthly_count'] + record['monthly_count']
                    counts['total_count'] += record['total_count']

                    await execute_query(
                        """
                        UPDATE statistics_handler 
                        SET daily_count = $1, weekly_count = $2, monthly_count = $3, 
                            total_count = $4, last_daily_update = $5, 
                            last_weekly_update = $6, last_monthly_update = $7
                        WHERE command = $8
                        """,
                        (counts['daily_count'], counts['weekly_count'],
                         counts['monthly_count'], counts['total_count'],
                         today, week_start, month_start, command)
                    )
                else:
                    await execute_query(
                        """
                        INSERT INTO statistics_handler 
                        (command, daily_count, weekly_count, monthly_count, total_count,
                         last_daily_update, last_weekly_update, last_monthly_update)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        (command, counts['daily_count'], counts['weekly_count'],
                         counts['monthly_count'], counts['total_count'],
                         today, week_start, month_start)
                    )

            self.cache.clear()
            self.last_flush = now


CALLBACK_COMMAND_MAPPING = {
    'get_dop_': 'Допы',
    'get_def_gpt_': 'Обычная трактовка',
    'get_day_spread_meaning_': 'Трактовка расклада дня',
    'day_meaning_day_': 'Трактовка карт дня',
    'add_referrals_': 'Трактовка карт дня',
    'admin_back_': 'Админ Команда',
    'admin_referrals_': 'Админ Команда',
    'admin_subscription_': 'Админ Команда',
    'admin_coupons_': 'Админ Команда',
    'sub_type_': 'Админ Команда',
    'admin_meanings_': 'Админ Команда',
    'coupon_type_': 'Админ Команда',
    'add_coupon_': 'Админ Команда',
    'manual_coupon_': 'Админ Команда',
    'manual_meanings_': 'Админ Команда',
    'cancel_subscription_': 'Админ Команда',
    'add_sub_': 'Админ Команда',
    'manual_sub_': 'Админ Команда',
    'manual_referrals_': 'Админ Команда',
}

ALLOWED_COMMANDS = {
    "библиотека", "доп", "мантра", "мтриплет", "помощь",
    "стриплет", "колода", "карта", "значение", "расклад",
    "допы", "триплет", "саб", "мой профиль", 'карта', 'настройки', 'услуги',
    "расклад на день", "расклад на неделю",
    "расклад на завтра", "расклад на месяц",
}

COMMAND_ALIASES = {
    "расклад дня": "расклад на день",
    "расклад недели": "расклад на неделю",
    "расклад месяца": "расклад на месяц",
    "расклад завтра": "расклад на завтра",
    "значение": "узнать значение",
}

ALLOWED_COMMANDS = {cmd.lower() for cmd in ALLOWED_COMMANDS}


def get_command_name(callback_data: str) -> str:
    callback_data = callback_data.lower()
    for command in sorted(ALLOWED_COMMANDS, key = len, reverse = True):
        if callback_data.startswith(command):
            return command
    for alias, standard in COMMAND_ALIASES.items():
        if callback_data.startswith(alias):
            return standard
    return callback_data


class HandlerStatisticsMiddleware(BaseMiddleware):
    def __init__(self, flush_interval: int = 60):
        self.stats_cache = StatisticsCache(flush_interval)

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        await self.stats_cache.start_auto_flush()  # Гарантируем запуск фоновой задачи

        if isinstance(event, Message):
            words = event.text.lower().split()[:3] if event.text else []
            command = "_".join(words) if words and words[0] in ALLOWED_COMMANDS else "unknown_message"
        elif isinstance(event, CallbackQuery):
            command = get_command_name(event.data)
        else:
            command = 'unknown_event'

        asyncio.create_task(self.stats_cache.increment(command))
        return await handler(event, data)
