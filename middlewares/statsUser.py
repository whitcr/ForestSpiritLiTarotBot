from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Dict, Any, Callable, Awaitable, Union
import keyboard as kb
from constants import DAILY_LIMIT
from database import execute_query, execute_select_all, execute_select
from filters.subscriptions import get_subscription
from datetime import datetime, timedelta


async def update_user_statistics(event: Message | CallbackQuery, bot) -> bool:
    if isinstance(event, Message):
        user_id = event.from_user.id
    elif isinstance(event, CallbackQuery):
        user_id = event.message.reply_to_message.from_user.id

    today = datetime.utcnow().date()
    week_start = today - timedelta(days = today.weekday())
    month_start = today.replace(day = 1)

    try:

        notification = await execute_select("SELECT notification FROM users WHERE user_id = $1", (user_id,))

        if notification == 0:
            await execute_query("UPDATE users SET notification = $1 WHERE user_id = $2", (True, user_id))
            await bot.send_message(user_id,
                                   "— Спасибо, что пользуетесь Ли. На данный момент был запущен тестовый режим крупного обновления, поэтому некоторый функционал был расширен, когда как другой будет доступен только при приобретении подписки. "
                                   "Если у вас возникли вопросы или проблемы, пишите в поддержку с помощью команды 'помощь'. Список команд -  https://telegra.ph/Lesnoj-Duh-Li-10-10")

        # Fetch the current counts and last update dates
        result = await execute_select_all(
            """
            SELECT daily_count, weekly_count, monthly_count, total_count,
                   last_daily_update, last_weekly_update, last_monthly_update
            FROM users
            WHERE user_id = $1
            """,
            (user_id,)
        )

        # Initialize user data if record is found
        if result and all(value is not None for value in result[0].values()):
            data = result[0]
            daily_count = data['daily_count'] if data['last_daily_update'] == today else 0
            weekly_count = data['weekly_count'] if data['last_weekly_update'] == week_start else 0
            monthly_count = data['monthly_count'] if data['last_monthly_update'] == month_start else 0
            total_count = data['total_count']
        else:
            daily_count = weekly_count = monthly_count = total_count = 0

        # Check subscription and daily limit
        if daily_count >= DAILY_LIMIT:
            result = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))
            if result == 0:
                return False  # User exceeded daily limit

        # Update counts
        daily_count += 1
        weekly_count += 1
        monthly_count += 1
        total_count += 1

        # Perform insert or update based on record existence
        if result:
            await execute_query(
                """
                UPDATE users
                SET daily_count = $1, weekly_count = $2, monthly_count = $3, total_count = $4,
                    last_daily_update = $5, last_weekly_update = $6, last_monthly_update = $7
                WHERE user_id = $8
                """,
                (daily_count, weekly_count, monthly_count, total_count,
                 today, week_start, month_start, user_id)
            )
        else:
            await execute_query(
                """
                INSERT INTO users 
                (user_id, daily_count, weekly_count, monthly_count, total_count,
                 last_daily_update, last_weekly_update, last_monthly_update, join_date)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                (user_id, daily_count, weekly_count, monthly_count, total_count,
                 today, week_start, month_start, today)
            )

    except Exception as e:
        return False

    return True


class UserStatisticsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Union[CallbackQuery, Message],
            data: Dict[str, Any]
    ) -> Any:
        bot = data.get("bot")
        if await update_user_statistics(event, bot):
            return await handler(event, data)
        else:
            if isinstance(event, Message):
                user_id = event.from_user.id
            elif isinstance(event, CallbackQuery):
                user_id = event.message.from_user.id
            await bot.send_message(user_id,
                                   text = "Ваш дневной лимит раскладов окончен. Возвращайтесь завтра или приобретите "
                                          "подписку с неограниченными раскладами",
                                   reply_markup = kb.sub_keyboard)
