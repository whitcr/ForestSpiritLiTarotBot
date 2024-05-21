from aiogram import types
from main import dp, bot
import keyboard as kb

from functions.createImage import text_size
from handlers.astrology.getMoon import get_moon_today
from handlers.tarot.spreads.getDaySpread import create_day_spread_image
from handlers.tarot.spreads.getWeekMonthSpread import create_image_six_cards
import pendulum
from io import BytesIO
from constants import FONT_S, FONT_M
import asyncio
from PIL import ImageDraw
import textwrap
from handlers.tarot.spreads.getDaySpread import create_day_keyboard


@dp.message_handler(lambda message: message.text.lower() == "рассылка")
async def day_follow(message: types.Message):
    await message.reply("Какую информацию вы хотите получать ежедневно?",
                        reply_markup = kb.follow_daily_mailing_keyboard)


async def moon_text_follow():
    try:
        text_moon = await get_moon_today()
        cursor.execute("select user_id from users where moon_follow=1;")
        for id in cursor.fetchall():
            user_id = id[0]
            await bot.send_message(user_id,
                                   f"Cегодня у нас: <b>{text_moon[1]}</b>\nФаза луны: <b>{text_moon[3]}</b>\nЗнак: <b>{text_moon[5]}</b>\nСозвездие: <b>{text_moon[7]}</b>\nЛунный день: <b>{text_moon[9]}</b>\nВидимость: <b>{text_moon[13]}</b>")

        text_moon.clear()
    except BotBlocked:
        cursor.execute("delete from users where user_id = {}".format(user_id))
        db.commit()
        pass
    except:
        pass


async def day_card_follow_schedule():
    date = pendulum.today('Europe/Kiev').format('DD.MM')
    cursor.execute("select user_id from users where day_card_follow=1;")
    for id in cursor.fetchall():
        try:
            user_id = id[0]
            try:
                cursor.execute(
                    "SELECT file_id FROM spreads_day WHERE user_id = %s AND date = %s",
                    (user_id, date)
                )
                file_id = cursor.fetchone()[0]

                cursor.execute(
                    f"select deck_type from spreads_day where user_id = {user_id} and date = '{date}' ")
                choice = cursor.fetchone()[0]
                if choice == 'raider':
                    keyboard = await create_day_keyboard(date)
                    msg = await bot.send_photo(user_id, photo = file_id, reply_markup = keyboard)
                    await asyncio.sleep(200)
                    try:
                        await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = msg.message_id,
                                                            reply_markup = None)
                    except:
                        pass
                else:
                    await bot.send_photo(user_id, photo = file_id)
            except:
                try:
                    cursor.execute("select username from users where user_id=%s;", (user_id,))
                    username = cursor.fetchone()[0]
                except:
                    username = user_id
                choice = await get_choice_spread(user_id)
                image, cards, affirmation_num = await create_day_spread_image(user_id,
                                                                              username, date)
                bio = BytesIO()
                bio.name = 'image.jpeg'
                with bio:
                    image.save(bio, 'JPEG')
                    bio.seek(0)
                    msg = await bot.send_photo(user_id, photo = bio)
                    file_id = msg.photo[-1].file_id

                    cursor.execute(
                        "INSERT INTO spreads_day (date, user_id, day_card, day_card_dop_1, day_card_dop,"
                        " day_conclusion, day_advice, day_aware, affirmation_of_day, file_id, deck_type) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (date, user_id, cards[0], cards[1], cards[2], cards[3], cards[4], cards[5],
                         affirmation_num, file_id, choice)
                    )

        except BotBlocked:
            cursor.execute("delete from users where user_id = {}".format(user_id))
            db.commit()
        except:
            pass


# async def random_message_schedule():
# Получаем количество пользователей в базе данных\
# МОЖНО ЗАПУСКАТЬ ЕГО УТРОМ И ЧТОБЫ ОН ВЫКЛЮЧАЛСЯ ПОД НОЧЬ ГДЕТО.
# user_count = db.count_users()
#
# # Вычисляем количество временных промежутков
# interval_count = max(user_count, 1)
# interval_secs = int(24 * 3600 / interval_count)
# interval_hours = max(interval_hours, 1)
# interval_secs = interval_secs // interval_hours
#
# while True:
#     # Выбираем случайный промежуток времени
#     random_interval = random.randint(0, interval_secs)
#
#     # Ожидаем выбранный промежуток времени
#     time.sleep(random_interval)
#
#     # Выбираем случайного пользователя
#     user = db.get_random_user()
#
#     # Отправляем сообщение пользователю
#     bot.send_message(user['chat_id'], 'Привет, {}!'.format(user['name']))


async def month_card_follow_schedule():
    cursor.execute("select user_id from users where week_card_follow=1;")
    for id in cursor.fetchall():
        try:
            user_id = id[0]
            try:
                cursor.execute("select username from users where user_id=%s;", (user_id,))
                username = cursor.fetchone()[0]
            except:
                username = user_id
            image, cards = await create_image_six_cards(user_id)
            draw_text = ImageDraw.Draw(image)

            draw_text.text((115, 245), 'Совет месяца', font = FONT_M, fill = 'white')
            draw_text.text((810, 10), 'Позитивные события', font = FONT_M, fill = 'white')
            draw_text.text((1574, 245), 'Угроза месяца', font = FONT_M, fill = 'white')
            draw_text.text((828, 514), 'Расклад на месяц', font = FONT_M, fill = 'white')
            draw_text.text((805, 1010), 'Негативные события', font = FONT_M, fill = 'white')
            draw_text.text((1295, 1025), 'from ForestSpiritLi', font = FONT_M, fill = 'white')

            para = textwrap.wrap(f"for {username}", width = 30)
            current_h, pad = 1050, 10
            draw_text = ImageDraw.Draw(image)
            for line in para:
                w, h = text_size(line, FONT_S)
                draw_text.text(((1910 - w) / 2, current_h), line, font = FONT_S)
                current_h += h + 110

            bio = BytesIO()
            bio.name = 'image.jpeg'
            with bio:
                image.save(bio, 'JPEG')
                bio.seek(0)
                msg = await bot.send_photo(user_id, photo = bio)
                file_id = msg.photo[-1].file_id
            cursor.execute(
                "insert into spreads_month (user_id, file_id) values ('{}', '{}')".format(user_id, file_id))
            db.commit()

            await asyncio.sleep(5)
        except:
            pass


async def week_card_follow_schedule():
    cursor.execute("select users.user_id from users where week_card_follow=1;")
    for id in cursor.fetchall():
        try:
            user_id = id[0]
            try:
                cursor.execute("select username from users where user_id=%s;", (user_id,))
                username = cursor.fetchone()[0]
            except:
                username = user_id
            image, cards = await create_image_six_cards(user_id)
            draw_text = ImageDraw.Draw(image)

            draw_text.text((115, 245), 'Совет недели', font = FONT_M, fill = 'white')
            draw_text.text((810, 10), 'Позитивные события', font = FONT_M, fill = 'white')
            draw_text.text((1574, 245), 'Угроза недели', font = FONT_M, fill = 'white')
            draw_text.text((828, 514), 'Расклад на неделю', font = FONT_M, fill = 'white')
            draw_text.text((805, 1010), 'Негативные события', font = FONT_M, fill = 'white')
            draw_text.text((1295, 1025), 'from ForestSpiritLi', font = FONT_M, fill = 'white')

            para = textwrap.wrap(f"for {username}", width = 30)
            current_h, pad = 1050, 10
            draw_text = ImageDraw.Draw(image)
            for line in para:
                w, h = text_size(line, FONT_S)
                draw_text.text(((1910 - w) / 2, current_h), line, font = FONT_S)
                current_h += h + 110

            bio = BytesIO()
            bio.name = 'image.jpeg'
            with bio:
                image.save(bio, 'JPEG')
                bio.seek(0)
                msg = await bot.send_photo(user_id, photo = bio)
                file_id = msg.photo[-1].file_id
            cursor.execute(
                "insert into spreads_week (user_id, file_id) values ('{}', '{}')".format(user_id, file_id))
            db.commit()

            await asyncio.sleep(5)
        except:
            pass


@dp.callback_query_handler(lambda call: call.data.endswith('follow_yes'))
async def daily_follow_yes(call: types.CallbackQuery):
    follow_type = call.data.replace('_yes', '')

    try:
        await call.answer()
        await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                    text = "Вы подписались!", reply_markup = kb.moon_follow_no_keyboard)

        cursor.execute(
            "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id",
            (call.from_user.id,))
        cursor.execute(f"UPDATE users SET {follow_type} = 1 WHERE user_id = %s;", (call.from_user.id,))
        db.commit()
    except Exception:
        pass


@dp.callback_query_handler(lambda call: call.data.endswith('follow_no'))
async def daily_follow_no(call: types.CallbackQuery):
    follow_type = call.data.replace('_no', '')

    try:
        await call.answer()
        await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                    text = "Позорник!")

        cursor.execute(f"UPDATE users SET {follow_type} = 0 WHERE user_id = %s;", (call.from_user.id,))
        db.commit()
    except Exception:
        pass
