from datetime import datetime
import aioschedule
import asyncio
import pendulum
from aiogram import Bot

from database import execute_query
from events.subscriptions.checkSubscription import check_subscriptions

from tech.mailing.dayCard import day_card_follow_schedule
from tech.mailing.monthSpread import month_card_follow_schedule
from tech.mailing.weekSpread import week_card_follow_schedule
from tech.posting.historyPracticePost import history_image
from tech.posting.meditationPost import get_meditation_post
from tech.posting.morningPost import morning_posting
from tech.posting.practiceCardPost import practice_choose_card_post, practice_choose_card_post_answer
from tech.posting.quizPost import practice_quiz_post
from tech.posting.statisticCards import get_statistic_post
from tech.posting.templates import notify_week_spread


async def schedule(bot, channel_id, admin_id):
    # ОЧИСТКА ТАБЛИЦ
    aioschedule.every().day.at("02:00").do(schedule_clean_day_card)
    aioschedule.every().monday.at("05:00").do(schedule_clean_week_tables)

    # РАССЫЛКА ПОЛЬЗОВАТЕЛЯМ
    aioschedule.every().day.at("07:01").do(lambda: asyncio.create_task(day_card_follow_schedule(bot)))
    aioschedule.every().monday.at("07:05").do(lambda: asyncio.create_task(week_card_follow_schedule(bot)))

    # ПЕРВЫЙ ДЕНЬ МЕСЯЦА
    aioschedule.every().day.at("05:00").do(lambda: asyncio.create_task(first_day_of_month(bot, channel_id)))

    # ПОСТЫ ДЛЯ КАНАЛА
    aioschedule.every().day.at("05:00").do(lambda: asyncio.create_task(morning_posting(bot, channel_id)))
    aioschedule.every().day.at("18:00").do(lambda: asyncio.create_task(get_statistic_post(bot, channel_id)))

    # aioschedule.every().day.at("08:00").do(daily_question)
    # aioschedule.every().day.at("12:00").do(random_card)

    aioschedule.every().monday.at("07:00").do(lambda: asyncio.create_task(notify_week_spread(bot, channel_id)))

    aioschedule.every().monday.at("14:00").do(lambda: asyncio.create_task(practice_quiz_post(bot, channel_id)))
    aioschedule.every().wednesday.at("14:00").do(lambda: asyncio.create_task(practice_quiz_post(bot, channel_id)))

    aioschedule.every().tuesday.at("14:00").do(
        lambda: asyncio.create_task(practice_choose_card_post(bot, channel_id, admin_id)))
    aioschedule.every().tuesday.at("17:00").do(
        lambda: asyncio.create_task(practice_choose_card_post_answer(bot, channel_id)))

    aioschedule.every().thursday.at("14:00").do(
        lambda: asyncio.create_task(practice_choose_card_post(bot, channel_id, admin_id)))
    aioschedule.every().thursday.at("17:00").do(
        lambda: asyncio.create_task(practice_choose_card_post_answer(bot, channel_id)))

    aioschedule.every().saturday.at("13:00 ").do(lambda: asyncio.create_task(history_image(bot, channel_id)))
    aioschedule.every().sunday.at("15:00").do(lambda: asyncio.create_task(get_meditation_post(bot, channel_id)))

    # ПОДПИСКИ
    aioschedule.every().day.at("10:00").do(lambda: asyncio.create_task(check_subscriptions(bot)))

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def schedule_clean_day_card():
    date = pendulum.yesterday('Europe/Kiev').format('DD.MM')
    await execute_query(
        'DELETE FROM spreads_day WHERE day IS NULL AND aware IS NULL AND advice IS NULL AND conclusion IS NULL AND '
        'date = $1',
        (date,))


async def schedule_clean_tables():
    # execute_query("TRUNCATE TABLE statistic_users")
    await execute_query("TRUNCATE TABLE statistic_cards")


async def schedule_clean_month_tables():
    await execute_query("TRUNCATE TABLE spreads_month")


async def schedule_clean_week_tables():
    await execute_query("TRUNCATE TABLE spreads_week")


async def schedule_month(bot: Bot, channel_id: str):
    await month_card_follow_schedule(bot)

    message = (f" — Пишем <b>'расклад на месяц'</b> и узнаем, чего опасаться и чего ждать от этого месяца. Чем больше "
               f"реакций, тем лучше карты!{channel_id}")
    await bot.send_message(channel_id, message)


def is_first_day_of_month():
    today = datetime.now()
    return today.day == 1


async def first_day_of_month(bot, channel_id):
    if is_first_day_of_month():
        await schedule_clean_month_tables()
        await schedule_month(bot, channel_id)
