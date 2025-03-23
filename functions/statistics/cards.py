import json
from typing import Union
from database import execute_query, execute_select, execute_select_all
from datetime import datetime, timedelta


async def get_statistic_card(num: Union[int, str]):
    now = datetime.utcnow()
    today = now.date()
    week_start = today - timedelta(days = today.weekday())
    month_start = today.replace(day = 1)

    name = await execute_select(
        """
        SELECT name
        FROM cards
        WHERE number = $1
        """,
        (num,)
    )

    result = await execute_select_all(
        """
        SELECT daily_count, weekly_count, monthly_count, total_count, 
               last_daily_update, last_weekly_update, last_monthly_update
        FROM statistics_cards 
        WHERE card = $1
        """,
        (name,)
    )

    if result:
        (daily_count, weekly_count, monthly_count, total_count,
         last_daily_update, last_weekly_update, last_monthly_update) = result[0]

        if last_daily_update != today:
            daily_count = 0
        if last_weekly_update != week_start:
            weekly_count = 0
        if last_monthly_update != month_start:
            monthly_count = 0

        await execute_query(
            """
            UPDATE statistics_cards 
            SET daily_count = $1, weekly_count = $2, monthly_count = $3, total_count = $4,
                last_daily_update =$5, last_weekly_update = $6, last_monthly_update =$7
            WHERE card = $8
            """,
            (daily_count + 1, weekly_count + 1, monthly_count + 1, total_count + 1,
             today, week_start, month_start, name)
        )
    else:
        await execute_query(
            """
            INSERT INTO statistics_cards 
            (card, daily_count, weekly_count, monthly_count, total_count,
             last_daily_update, last_weekly_update, last_monthly_update)
            VALUES ($1, 1, 1, 1, 1, $2, $3, $4)
            """,
            (name, today, week_start, month_start)
        )


async def get_user_card_statistics(user_id: int, num: int):
    now = datetime.utcnow()
    today = now.date()
    week_start = today - timedelta(days = today.weekday())
    month_start = today.replace(day = 1)

    result = await execute_select_all(
        """
        SELECT daily_stats_cards, weekly_stats_cards, monthly_stats_cards, total_stats_cards, 
               last_daily_update_cards, last_weekly_update_cards, last_monthly_update_cards
        FROM users
        WHERE user_id = $1
        LIMIT 1
        """,
        (user_id,)
    )

    def update_json_stats(stats, card_num):
        num_str = str(card_num)
        stats[num_str] = stats.get(num_str, 0) + 1
        return stats

    if result and any(record for record in result if any(value is not None for value in record.values())):
        (daily_stats_json, weekly_stats_json, monthly_stats_json, total_stats_json,
         last_daily_update, last_weekly_update, last_monthly_update) = result[0]

        daily_stats = json.loads(daily_stats_json) if daily_stats_json else {}
        weekly_stats = json.loads(weekly_stats_json) if weekly_stats_json else {}
        monthly_stats = json.loads(monthly_stats_json) if monthly_stats_json else {}
        total_stats = json.loads(total_stats_json) if total_stats_json else {}

        if last_daily_update != today:
            daily_stats = {}
        if last_weekly_update != week_start:
            weekly_stats = {}
        if last_monthly_update != month_start:
            monthly_stats = {}

    else:
        daily_stats = {}
        weekly_stats = {}
        monthly_stats = {}
        total_stats = {}

    daily_stats = update_json_stats(daily_stats, num)
    weekly_stats = update_json_stats(weekly_stats, num)
    monthly_stats = update_json_stats(monthly_stats, num)
    total_stats = update_json_stats(total_stats, num)

    daily_stats_json = json.dumps(daily_stats)
    weekly_stats_json = json.dumps(weekly_stats)
    monthly_stats_json = json.dumps(monthly_stats)
    total_stats_json = json.dumps(total_stats)

    await execute_select(
        """
        INSERT INTO users 
        (user_id, daily_stats_cards, weekly_stats_cards, monthly_stats_cards, total_stats_cards,
         last_daily_update_cards, last_weekly_update_cards, last_monthly_update_cards)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (user_id) DO UPDATE SET
        daily_stats_cards = $2,
        weekly_stats_cards = $3,
        monthly_stats_cards = $4,
        total_stats_cards = $5,
        last_daily_update_cards = $6,
        last_weekly_update_cards = $7,
        last_monthly_update_cards = $8
        """,
        (user_id, daily_stats_json, weekly_stats_json, monthly_stats_json, total_stats_json,
         today, week_start, month_start)
    )
