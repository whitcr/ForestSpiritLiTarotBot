from datetime import timedelta, datetime

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Dict, Any, Callable, Awaitable
from database import execute_query, execute_select_all


async def process_callback_data_to_name(callback_data):
    if 'get_dop_' in callback_data:
        return 'Допы'
    elif 'get_default_meaning_gpt_' in callback_data:
        return 'Обычная трактовка'
    elif 'get_day_spread_meaning_' in callback_data:
        return 'Трактовка расклада дня'
    elif 'day_meaning_day_' in callback_data:
        return 'Трактовка карт дня'
    return callback_data


async def update_statistics(command: str):
    now = datetime.utcnow()
    today = now.date()
    week_start = today - timedelta(days = today.weekday())
    month_start = today.replace(day = 1)
    command = command.lower()
    # Проверяем существование записи и получаем текущие значения
    result = await execute_select_all(
        """
        SELECT daily_count, weekly_count, monthly_count, total_count, 
               last_daily_update, last_weekly_update, last_monthly_update
        FROM statistics_handler 
        WHERE command = $1
        """,
        (command,)
    )

    if result and any(record for record in result if any(value is not None for value in record.values())):
        (daily_count, weekly_count, monthly_count, total_count,
         last_daily_update, last_weekly_update, last_monthly_update) = result[0]

        # Сбрасываем счетчики, если начался новый период
        if last_daily_update != today:
            daily_count = 0
        if last_weekly_update != week_start:
            weekly_count = 0
        if last_monthly_update != month_start:
            monthly_count = 0

        # Увеличиваем счетчики
        await execute_query(
            """
            UPDATE statistics_handler 
            SET daily_count = $1, weekly_count = $2, monthly_count = $3, total_count = $4,
                last_daily_update = $5, last_weekly_update = $6, last_monthly_update = $7
            WHERE command = $8
            """,
            (daily_count + 1, weekly_count + 1, monthly_count + 1, total_count + 1,
             today, week_start, month_start, command)
        )
    else:
        # Создаем новую запись
        await execute_query(
            """
            INSERT INTO statistics_handler 
            (command, daily_count, weekly_count, monthly_count, total_count,
             last_daily_update, last_weekly_update, last_monthly_update)
            VALUES ($1, 1, 1, 1, 1, $2, $3, $4)
            """,
            (command, today, week_start, month_start)
        )


class HandlerStatisticsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            command = event.text.split()[0] if event.text else 'unknown_message'
        elif isinstance(event, CallbackQuery):
            command = await process_callback_data_to_name(event.data)
        else:
            command = 'unknown_event'

        await update_statistics(command)
        return await handler(event, data)
