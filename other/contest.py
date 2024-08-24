from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# КОНКУРСНОЕ МЕНЮ
contest_ticket = InlineKeyboardButton(text = "Мой билет", callback_data = "get_contest_ticket")
contest_url = InlineKeyboardButton(text = "Подарок за друзей", callback_data = "get_contest_url")

contest_keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 1).add(contest_ticket, contest_url)
from aiogram.dispatcher.filters import IDFilter
import keyboard as kb
from bot import cursor, db
from bot import dp, bot
from aiogram import Bot, types
from io import BytesIO
from PIL import Image, ImageDraw
from PIL import ImageFont
# from functions.middlewares import check_subscription_contest
from handlers.tarot.spreads.getSpreads import get_image_three_cards
from constants import FONT_L
from chatGPT.getGPT import time_spread
from constants import ADMIN_ID, CHANNEL_ID

FONT = ImageFont.truetype("./cards/tech/fonts/1246-font.otf", 90)
import time
from aiogram.utils.exceptions import BotBlocked


@dp.message_handler(lambda message: message.text.lower() == "конкурс")
async def join_contest(message: types.Message):
    try:
        user_id = message.from_user.id
        if await check_subscription_contest(message.from_user.id):
            try:
                cursor.execute("SELECT user_id FROM users_contest WHERE user_id = %s", (str(user_id),))
                row = cursor.fetchone()
                if row:
                    await bot.send_message(user_id, "Ты участвуешь конкурсе!", reply_markup = contest_keyboard)
                else:
                    try:
                        username = message.from_user.username
                        firstname = message.from_user.first_name
                        cursor.execute("INSERT INTO users_contest (user_id, username, firstname) VALUES (%s, %s, %s)",
                                       (str(user_id), username, firstname))
                        db.commit()
                        cursor.execute("select number from users_contest where user_id ='{}';".format(user_id))
                        number = cursor.fetchone()[0]
                        if number <= 9:
                            number = "0" + str(number)
                        image = Image.open("contest_ticket.png")
                        draw_text = ImageDraw.Draw(image)
                        draw_text.text((45, 850), f'{number}', font = FONT, fill = 'white')

                        bio = BytesIO()
                        bio.name = 'image.png'
                        image.save(bio, 'PNG')
                        bio.seek(0)

                        await bot.send_photo(user_id, photo = bio)
                        await bot.send_message(user_id,
                                               "Поздравляю, ты теперь участник конкурса! Тебя ждет много интересных призов!",
                                               reply_markup = contest_keyboard)
                    except:
                        await bot.send_message(user_id, "Если тебе не пришел билет, нажми на кнопку 'Мой билет'",
                                               reply_markup = contest_keyboard)
                        pass
            except:
                await bot.send_message(user_id, "Если тебе не пришел билетик, нажми на кнопку 'Мой билет'",
                                       reply_markup = contest_keyboard)
                pass
        else:
            await message.reply(
                text = 'Подпишитесь на каналы ниже, чтобы участвовать в конкурсе.',
                reply_markup = kb.follow_contest_keyboard)
    except:
        pass


@dp.callback_query_handler(lambda c: c.data.startswith('get_contest_ticket'))
async def process_callback_get_contest_ticket(call: types.CallbackQuery):
    await call.answer()
    try:

        user_id = call.from_user.id

        cursor.execute("SELECT user_id FROM users_contest WHERE user_id = %s", (str(user_id),))
        row = cursor.fetchone()
        if row:
            cursor.execute("select number from users_contest where user_id ='{}';".format(str(user_id)))
            number = cursor.fetchone()[0]
            if number <= 9:
                number = "0" + str(number)
            image = Image.open("contest_ticket.png")
            draw_text = ImageDraw.Draw(image)
            draw_text.text((45, 850), f'{number}', font = FONT, fill = 'white')

            bio = BytesIO()
            bio.name = 'image.png'
            image.save(bio, 'PNG')
            bio.seek(0)

            await bot.send_photo(user_id, photo = bio)
        else:
            username = call.from_user.username
            cursor.execute("INSERT INTO users_contest (user_id, username) VALUES (%s, %s)", (str(user_id), username))
            cursor.execute("select number from users_contest where user_id ='{}';".format(str(user_id)))
            number = cursor.fetchone()[0]
            if number <= 9:
                number = "0" + str(number)
            image = Image.open("contest_ticket.png")
            draw_text = ImageDraw.Draw(image)
            draw_text.text((45, 850), f'{number}', font = FONT, fill = 'white')

            bio = BytesIO()
            bio.name = 'image.png'
            image.save(bio, 'PNG')
            bio.seek(0)

            await bot.send_photo(user_id, photo = bio)
    except:
        await bot.send_message(user_id,
                               "Что-то пошло не так, попробуй еще раз или обратись к администрации @wandererinwoods",
                               reply_markup = contest_keyboard)
        pass


@dp.callback_query_handler(lambda c: c.data.startswith('check_contest_follow'))
async def process_callback_check_contest_follow(call: types.CallbackQuery):
    await call.answer()
    check = await check_subscription_contest(call.from_user.id)
    if check:
        await join_contest(call)
    else:
        await bot.send_message(call.from_user.id, "Ты не подписался на все каналы.")


# @dp.message_handler(lambda message: message.text.lower() == "тест")
async def get_year_spread(user_id):
    await bot.send_message(user_id,
                           "Спасибо за участие и приглашенных друзей, вот твой подарок - РАСКЛАД НА ЯНВАРЬ МЕСЯЦ!")

    MONTH_MAP = ["Января"]

    THEME_MAP = ["Финансы", "Личная Жизнь", "Эмоции"]

    for MONTH in MONTH_MAP:
        image, num = await get_image_three_cards(user_id)
        draw_text = ImageDraw.Draw(image)

        draw_text.text((230, 80), f"Карта {MONTH}", fill = 'white', font = FONT_L)
        draw_text.text((820, 80), f"Угроза {MONTH}", fill = 'white', font = FONT_L)
        draw_text.text((1450, 80), f"Совет {MONTH}", fill = 'white', font = FONT_L)

        bio = BytesIO()
        bio.name = 'image.jpeg'
        with bio:
            image.save(bio, 'JPEG')
            bio.seek(0)
            await bot.send_photo(user_id, photo = bio)

        msg = await bot.send_message(user_id, "Трактую..")
        text = await time_spread(num, "месяц")
        text = f"<b>ТРАКТОВКА РАСКЛАДА</b>\n\n{text}"
        await bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text = text)

        for THEME in THEME_MAP:
            image, num = await get_image_three_cards(user_id)
            draw_text = ImageDraw.Draw(image)

            draw_text.text((820, 80), f"{THEME} {MONTH}", fill = 'white', font = FONT_L)

            bio = BytesIO()
            bio.name = 'image.jpeg'
            with bio:
                image.save(bio, 'JPEG')
                bio.seek(0)
                await bot.send_photo(user_id, photo = bio)

            msg = await bot.send_message(user_id, "Трактую..")
            text = await time_spread(num, "месяц", THEME)
            text = f"<b>ТРАКТОВКА РАСКЛАДА</b>\n\n{text}"
            await bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text = text)

    await bot.send_message(user_id,
                           "Удачи тебе в конкурсе!")


# CHANNEL_IDS = ["@forestspirito"]
CHANNEL_IDS = ["@forestspirito", "@SoulMatrixTarot", "@semirechenko", "@sisuritiTarot", "@tarosmashey"]

CHAT_ID = -1001894916266


async def check_subscription_contest(user):
    try:
        chat_members = [await bot.get_chat_member(chat_id = channel_id, user_id = user) for channel_id in CHANNEL_IDS]

        subscribed_to_all = all(
            status in [types.ChatMemberStatus.MEMBER, types.ChatMemberStatus.CREATOR,
                       types.ChatMemberStatus.ADMINISTRATOR]
            for status in [chat_member.status for chat_member in chat_members]
        )

        return subscribed_to_all
    except:
        return False


@dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!проверка"))
async def rassylka_uns_contest(message: types.Message):
    cursor.execute("select user_id from users_contest")

    count = 0
    count1 = 0

    cursor.execute("select user_id from users_contest")
    for id in cursor.fetchall():
        user_id = id[0]
        if await check_subscription_contest(user_id):
            pass
        else:
            try:
                await bot.send_message(user_id, f"— Спасибо тебе за участие в конкурсе, но я вижу, "
                                                "что ты отписался от каналов. \n\n Если ты хочешь получать бесплатные"
                                                " подарки и продолжать участвовать в новогоднем конкурсе — подпишись на все каналы.",
                                       reply_markup = kb.follow_contest_keyboard)
                count = count + 1
                time.sleep(1)
            except BotBlocked:
                count1 = count1 + 1
            except:
                pass

    await bot.send_message(504890623, text = f"Отписалось {count} пользователя. {count1} заблокировали Ли.")


@dp.message_handler(content_types = ['text'])
async def save_other(message: types.Message):
    try:
        # Get information about the message
        user_id = message.from_user.id
        chat_id = message.chat.id
        message_text = message.text

        # Reply with the information
        reply_text = (
            f"User ID: {user_id}\n"
            f"Chat ID: {chat_id}\n"
            f"Message Text: {message_text}"
        )
        await message.reply(reply_text)

    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# @dp.message_handler(content_types = ['photo'])
# async def save_other(message: types.Message):
#     try:
#         file = message.photo[-1].file_id
#         await message.reply(f"{file}")
#
#     except:
#         await message.reply("Не нервируй меня.")

#
# @dp.message_handler(content_types = ['video'])
# async def save_other(message: types.Message):
#     try:
#         file = message.video.file_id
#         await message.reply(f"{file}")
#
#     except:
#         await message.reply("Не нервируй меня.")

# @dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!тест"))
# async def posting_memes(message: types.Message):
#     try:

# media = ["AgACAgIAAxkBAAE56R1leGII6F84xjzM3rl-rK6MEGk8HgACXdgxG2chYUtZhtCkKYczSQEAAwIAA3gAAzME" ,
#          "AgACAgIAAxkBAAE56R5leGIIwQABCJr4I3PvpgHOmRRDuRsAAl7YMRtnIWFLerpsb8alGp8BAAMCAAN4AAMzBA" ,
#          "AgACAgIAAxkBAAE56R9leGIIdvomAbgf4R6RybODvRhUxQACX9gxG2chYUuLTq2WdPTMwQEAAwIAA3gAAzME" ,
#          "AgACAgIAAxkBAAE56SBleGII_J1I_T3IkG3q5sApz7ikggACYNgxG2chYUsMNrmidZ5PbwEAAwIAA3gAAzME" ,
#          "AgACAgIAAxkBAAE56SFleGIImphjT9Y_OhPmxDbFWd7ATQACYdgxG2chYUuXkc3icxVbcQEAAwIAA3gAAzME" ,
#          "AgACAgIAAxkBAAE56SJleGIIvTCmAAGZPIy9MTDF8g59cPYAAmLYMRtnIWFLWH-Mev9QKHEBAAMCAAN4AAMzBA"]

# group = types.MediaGroup()
# for image in media:
#     group.attach_photo(photo=image)
#     db.commit()

# except:
#     pass


# @dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!подарок"))
# async def rassylka_gifts_contest(message: types.Message):
#
#         count = 0
#         count1 = 0
#
#         cursor.execute("select user_id from users_contest")
#         for id in cursor.fetchall():
#             try:
#                     user_id = id[0]
#                 # if await check_subscription_contest(user_id):
#                     try:
#                         video = "BAACAgIAAxkBAAE7HdVlgYDz6ihyxHvXJnQpVgstOP9CFAAC3zkAAua-CUh9o-uG6LAFgDME"
#                         await bot.send_video(chat_id = user_id, video = video)
#
#                         await bot.send_message(user_id, f"— Вот твой второй подарок с новогоднего конкурса! Узнай, что может блокировать деньги в твоей матрице судьбы! Спасибо, что ты с нами :)")
#                         count += 1
#
#                         time.sleep(1)
#                     except:
#                         count1 += 1
#                         pass
#             except:
#                 count1 += 1
#                 pass
#             # else:
#             #     count1 += 1
#             #     await bot.send_message(user_id,
#             #                            f"—  Я рассылал подарки, но заметил, что ты не подписан на каналы, которые организовали конкурс. Если хочешь получать следующие подарки, подпишись :)", reply_markup = kb.follow_contest_keyboard)
#
#         await bot.send_message(504890623, text = f"Подарок получили {count} пользователя. {count1} не получили.")

# @dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!подарок"))
# async def rassylka_gifts_contest(message: types.Message):
#
#         count = 0
#         count1 = 0
#
#         cursor.execute("select user_id from users_contest")
#         for id in cursor.fetchall():
#             try:
#                     user_id = id[0]
#                 # if await check_subscription_contest(user_id):
#                     try:
#                         document = "BQACAgIAAxkBAAE9XZ5lkBOrWyGwyqNXvEibsRcqln72bwACS0MAAmPPcUj5yAvVqATGyTQE"
#                         await bot.send_document(chat_id = user_id, document = document)
#
#                         await bot.send_message(user_id, f"— С Наступающим! Вот твой четвертый подарок в нашем новогоднем конкурсе! Спасибо, что ты с нами :) Уже завтра будут известны победителя конкурса! ")
#                         count += 1
#
#                         time.sleep(1)
#                     except:
#                         count1 += 1
#                         pass
#             except:
#                 count1 += 1
#                 pass
#             # else:
#             #     count1 += 1
#             #     await bot.send_message(user_id,
#             #                            f"—  Я рассылал подарки, но заметил, что ты не подписан на каналы, которые организовали конкурс. Если хочешь получать следующие подарки, подпишись :)", reply_markup = kb.follow_contest_keyboard)
#
#         await bot.send_message(504890623, text = f"Подарок получили {count} пользователя. {count1} не получили.")


#
# @dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!конкурс"))
# async def rassylka(message: types.Message):
#     # text = message.text.split()[1:]
#     post = "—  Спасибо за участие в новогоднем конкурсе! Ты можешь получить подарок в виде БЕСПЛАТНОГО расклада на Январь месяц, " \
#            "если пригласишь ТРОИХ друзей участвовать в конкурсе! Жми 'подарок за друзей' и отправляй им свою ссылку"
#
#     cursor.execute("select user_id from users_contest")
#
#     count = 0
#     count1 = 0
#
#     for id in cursor.fetchall():
#         try:
#             user_id = id[0]
#             await bot.send_message(user_id, post, reply_markup = contest_keyboard)
#             count = count + 1
#             time.sleep(1)
#         except BotBlocked:
#             count1 = count1 + 1
#         except:
#             сount1 = count1 + 1
#         db.commit()
#
#     await bot.send_message(504890623, text = f"Сообщение получили {count} пользователя. {count1} заблокировали Ли.")
