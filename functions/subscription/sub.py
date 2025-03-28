from datetime import datetime, timedelta
import pytz

from database import execute_query, execute_select_all, execute_select


async def give_sub(user_id, days, sub_type):
    current_sub_data = await execute_select(
        "SELECT subscription_date FROM users WHERE user_id = $1", (user_id,)
    )

    current_sub_type = await execute_select(
        "SELECT subscription FROM users WHERE user_id = $1", (user_id,)
    )

    if current_sub_data and current_sub_type == sub_type:
        date = current_sub_data + timedelta(days = days)
    else:
        date = datetime.now(pytz.timezone('Europe/Kiev')).date() + timedelta(days = days)

    await execute_query(
        "UPDATE users SET subscription = $1, subscription_date = $2 WHERE user_id = $3",
        (sub_type, date, user_id)
    )

    await give_sub_meanings(user_id, sub_type, days)

    return date


async def give_sub_meanings(user_id, sub, days):
    amount_per_30_days = {1: 100, 2: 200, 3: 300}.get(sub, 0)

    if amount_per_30_days == 0:
        return 0

    total_amount = (amount_per_30_days / 30) * days

    await execute_query("update users set paid_meanings = paid_meanings + $1 where user_id = $2",
                        (total_amount, user_id,))

    return total_amount


async def give_meanings(user_id, amount):
    await execute_query("update users set paid_meanings = paid_meanings + $1 where user_id = $2", (amount, user_id,))
