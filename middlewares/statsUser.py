from functools import wraps
from aiogram.types import Message, CallbackQuery
from typing import Callable, Awaitable, Any, Union
import keyboard as kb
from database import execute_query, execute_select_all, execute_select
from constants import DAILY_LIMIT
from datetime import datetime, timedelta


async def update_user_statistics(event: Union[Message, CallbackQuery], bot) -> bool:
    user_id = event.from_user.id
    today = datetime.utcnow().date()
    week_start = today - timedelta(days = today.weekday())
    month_start = today.replace(day = 1)

    await notify_user(user_id, bot)

    result = await execute_select_all(
        """
        SELECT daily_count, weekly_count, monthly_count, total_count,
               last_daily_update, last_weekly_update, last_monthly_update
        FROM users
        WHERE user_id = $1
        """,
        (user_id,)
    )

    if result and all(value is not None for value in result[0].values()):
        data = result[0]
        daily_count = data['daily_count'] if data['last_daily_update'] == today else 0
        weekly_count = data['weekly_count'] if data['last_weekly_update'] == week_start else 0
        monthly_count = data['monthly_count'] if data['last_monthly_update'] == month_start else 0
        total_count = data['total_count']
    else:
        daily_count = weekly_count = monthly_count = total_count = 0

    if daily_count >= DAILY_LIMIT:
        result = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))
        if result == 0:
            return False

    daily_count += 1
    weekly_count += 1
    monthly_count += 1
    total_count += 1

    if result:
        await execute_query(
            """
            UPDATE users
            SET daily_count = $1, weekly_count = $2, monthly_count = $3, total_count = $4,
                last_daily_update = $5, last_weekly_update = $6, last_monthly_update = $7
            WHERE user_id = $8
            """,
            (daily_count, weekly_count, monthly_count, total_count, today, week_start, month_start, user_id)
        )

        us = await execute_select("SELECT username FROM users WHERE user_id = $1", (user_id,))

        if not us:
            username = event.from_user.username if event.from_user.username else "Без ника"
            name = event.from_user.full_name if event.from_user.full_name else "Без имени"
            await execute_query(
                """
                UPDATE users
                SET username = $1, name = $2
                WHERE user_id = $3
                """,
                (username, name, user_id)
            )
    else:
        username = event.from_user.username if event.from_user.username else "Без ника"
        name = event.from_user.full_name if event.from_user.full_name else "Без имени"

        await execute_query(
            """
            INSERT INTO users 
            (user_id, username, name, cards_type, daily_count, weekly_count, monthly_count, total_count,
             last_daily_update, last_weekly_update, last_monthly_update, join_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, &10, $11, $12)
            """,
            (user_id, username, name, 'raider', daily_count, weekly_count, monthly_count, total_count, today,
             week_start,
             month_start, today)
        )

    return True


def use_user_statistics(handler: Callable[..., Awaitable[Any]]):
    @wraps(handler)
    async def wrapper(event: Union[Message, CallbackQuery], *args, **kwargs):

        bot = event.bot
        if not bot:
            raise ValueError("Bot instance is required for use_user_statistics")

        if not await update_user_statistics(event, bot):
            user_id = event.from_user.id
            await bot.send_message(
                user_id,
                text = "Ваш дневной лимит раскладов окончен. Возвращайтесь завтра или приобретите подписку.",
                reply_markup = kb.sub_keyboard
            )
            return

        return await handler(event, *args, **kwargs)

    return wrapper


async def notify_user(user_id, bot):
    notification = await execute_select("SELECT notification FROM users WHERE user_id = $1", (user_id,))

    if notification == 0:
        await execute_query("UPDATE users SET notification = $1 WHERE user_id = $2", (True, user_id))
        await execute_query("UPDATE users SET paid_meanings = paid_meanings + 10 WHERE user_id = $1", (user_id,))
        await bot.send_message(user_id,
                               "— Спасибо, что пользуетесь Ли. На данный момент был запущен тестовый режим крупного обновления, поэтому некоторый функционал был расширен, "
                               "тогда как другой будет доступен только при приобретении подписки. \n"
                               "Если у вас возникли вопросы или проблемы, пишите в поддержку с помощью команды 'помощь'. Список команд -  https://telegra.ph/Lesnoj-Duh-Li-10-10 \n\n"
                               "В качестве бонуса вам были начислены 10 индивидуальных трактовок, чтобы вы могли попробовать новый функционал.",
                               reply_markup = kb.menu_private_keyboard)
