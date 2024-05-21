from aiogram.dispatcher.filters import IDFilter
import time
from bot import dp, bot, cursor, db
from constants import ADMIN_ID
from aiogram import types
from aiogram.utils.markdown import hlink
from aiogram.utils.exceptions import BotBlocked


@dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("кто"))
async def posting_trilpet_answer(message: types.Message):
    user = message.text.split()
    user = f"<a href = 'tg://user?id={user[1]}'>чел</a>"
    text = f"Вот этот вот {user}"
    await message.reply(text)


@dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!всем"))
async def rassylka(message: types.Message):
    link = message.text.split()[1]
    wordlink = message.text.split()[2]
    text = message.text.split()[3:]
    llink = hlink(wordlink, link)
    post = "— " + llink + " " + str(text)

    post = post.replace("'", "").replace(",", "").replace("[", "").replace("]", "")

    cursor.execute("select user_id from users")

    count = 0
    count1 = 0

    for id in cursor.fetchall():
        try:
            user_id = id[0]
            await bot.send_message(user_id, post)
            count = count + 1
            time.sleep(1)
        except BotBlocked:
            user_id = id[0]
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            count1 = count1 + 1
        except:
            user_id = id[0]
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        db.commit()

    await bot.send_message(504890623, text = f"Сообщение получили {count} пользователя. {count1} заблокировали Ли.")


@dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.startswith("!!всем"))
async def rassylka1(message: types.Message):
    text = message.text.split()[1:]
    post = "— " + " " + str(text)
    post = post.replace("'", "").replace(",", "").replace("[", "").replace("]", "")

    count = 0
    count1 = 0

    for id in cursor.fetchall():
        try:
            user_id = id[0]
            # print(user_id)
            await bot.send_message(user_id, post)
            count = count + 1
            time.sleep(1)
        except:
            count1 = count1 + 1
            pass
    await bot.send_message(504890623,
                           text = f"Сообщение было отослано {count} пользователям. {count1} заблокировали Ли.")


@dp.message_handler(IDFilter(user_id = ADMIN_ID), lambda message: message.text.lower() == "пока, дружок")
async def get_ban(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        if not message.reply_to_message:
            await message.reply("Отправь эту команду ответом на сообщение нарушителя.")
        else:
            try:
                replied_user = message.reply_to_message.from_user.id
                name_user = message.reply_to_message.from_user.first_name
                await bot.kick_chat_member(chat_id = message.chat.id, user_id = replied_user)
                await bot.send_message(chat_id = message.chat.id, text = f"Дружок {name_user} забанен, радуемся.")
            except:
                pass


@dp.message_handler(lambda message: message.text.lower() == "айди")
async def get_id(message: types.Message):
    await bot.send_message(504890623,
                           text = f"{message.from_user.id} - {message.from_user.first_name}")
