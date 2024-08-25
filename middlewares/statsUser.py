from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Dict, Any, Callable, Awaitable, Union

from constants import DAILY_LIMIT
from database import execute_query, execute_select_all
from datetime import datetime, timedelta

from filters.subscriptions import get_subscription


async def update_user_statistics(event: Message) -> bool:
    user_id = event.from_user.id
    now = datetime.utcnow()
    today = now.date()
    week_start = today - timedelta(days = today.weekday())
    month_start = today.replace(day = 1)

    try:
        result = await execute_select_all(
            """
            SELECT daily_count, weekly_count, monthly_count, total_count,
                   last_daily_update, last_weekly_update, last_monthly_update
            FROM users
            WHERE user_id = $1
            """,
            (user_id,)
        )

        if result and any(record for record in result if any(value is not None for value in record.values())):
            (daily_count, weekly_count, monthly_count, total_count,
             last_daily_update, last_weekly_update, last_monthly_update) = result[0]

            if last_daily_update != today:
                daily_count = 0
            if last_weekly_update != week_start:
                weekly_count = 0
            if last_monthly_update != month_start:
                monthly_count = 0

            subscription = await get_subscription(user_id, 0)
            if subscription and daily_count >= DAILY_LIMIT:
                return False

            await execute_query(
                """
                UPDATE users
                SET daily_count = $1, weekly_count = $2, monthly_count = $3, total_count = $4,
                    last_daily_update = $5, last_weekly_update = $6, last_monthly_update = $7
                WHERE user_id = $8
                """,
                (daily_count + 1, weekly_count + 1, monthly_count + 1, total_count + 1,
                 today, week_start, month_start, user_id)
            )
        else:
            try:
                await execute_query(
                    """
                    UPDATE users
                    SET daily_count = 1, weekly_count = 1, monthly_count = 1, total_count = 1,
                        last_daily_update = $1, last_weekly_update = $2, last_monthly_update = $3
                    WHERE user_id = $4
                    """,
                    (today, week_start, month_start, user_id)
                )
            except:
                await execute_query(
                    """
                    INSERT INTO users
                    (user_id, daily_count, weekly_count, monthly_count, total_count,
                     last_daily_update, last_weekly_update, last_monthly_update)
                    VALUES ($4, 1, 1, 1, 1, $1, $2, $3)
                    """,
                    (today, week_start, month_start, user_id)
                )
    except Exception as e:
        pass

    return True


class UserStatisticsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Union[CallbackQuery, Message],
            data: Dict[str, Any]
    ) -> Any:
        if await update_user_statistics(event):
            return await handler(event, data)
        else:
            bot = data.get("bot")
            user_id = event.from_user.id
            chat_id = event.chat.id
            await bot.send_message(chat_id, user_id, "Limit exceeded")
