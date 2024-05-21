from bot import dp, db, bot, cursor
import aioschedule
import asyncio
import pendulum
from tech.posting.getDailyPosts import morning_posting, get_statistic_post, practice_quiz_post, notify_week_spread,\
    practice_choose_card_post, practice_choose_card_post_answer, history_image, get_meditation_post
from .getDailyMailing import day_card_follow_schedule, week_card_follow_schedule
from aiogram.dispatcher.filters import IDFilter
from constants import ADMIN_ID, CHANNEL_ID
from chatGPT.getGPT import daily_question, random_card


async def schedule():
    # ОЧИСТКА ТАБЛИЦ
    aioschedule.every().day.at("02:00").do(schedule_clean_day_card)
    aioschedule.every().monday.at("05:00").do(schedule_clean_week_tables)

    # РАССЫЛКА ПОЛЬЗОВАТЕЛЯМ
    aioschedule.every().day.at("05:01").do(day_card_follow_schedule)
    aioschedule.every().monday.at("05:05").do(week_card_follow_schedule)

    # ПОСТЫ ДЛЯ КАНАЛА
    aioschedule.every().day.at("05:00").do(morning_posting)
    aioschedule.every().day.at("18:00").do(get_statistic_post)

    aioschedule.every().day.at("08:00").do(daily_question)
    aioschedule.every().day.at("12:00").do(random_card)

    aioschedule.every().monday.at("07:00").do(notify_week_spread)

    aioschedule.every().monday.at("14:00").do(practice_quiz_post)
    aioschedule.every().wednesday.at("14:00").do(practice_quiz_post)

    aioschedule.every().tuesday.at("14:00").do(practice_choose_card_post)
    aioschedule.every().tuesday.at("17:00").do(practice_choose_card_post_answer)

    aioschedule.every().thursday.at("14:00").do(practice_choose_card_post)
    aioschedule.every().thursday.at("17:00").do(practice_choose_card_post_answer)

    aioschedule.every().saturday.at("13:00 ").do(history_image)
    aioschedule.every().sunday.at("15:00").do(get_meditation_post)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def schedule_clean_day_card():
    date = pendulum.yesterday('Europe/Kiev').format('DD.MM')
    cursor.execute(
        'DELETE FROM spreads_day WHERE day IS NULL AND aware IS NULL AND advice IS NULL AND conclusion IS NULL AND date = %s',
        (date,))


async def schedule_clean_tables():
    # cursor.execute("TRUNCATE TABLE statistic_users")
    cursor.execute("TRUNCATE TABLE statistic_cards")

    db.commit()


async def schedule_clean_month_tables():
    cursor.execute("TRUNCATE TABLE spreads_month")
    db.commit()


async def schedule_clean_week_tables():
    cursor.execute("TRUNCATE TABLE spreads_week")
    db.commit()


@dp.message_handler(IDFilter(user_id = ADMIN_ID), lambda message: message.text.lower().startswith("!расклмесяц"))
async def schedule_month(self):
    await schedule_clean_month_tables()
    message = f" — Пишем <b>'расклад на месяц'</b> и узнаем, чего опасаться и чего ждать от этого месяца. Чем больше реакций, тем лучше карты!"
    await bot.send_message(CHANNEL_ID, message)
