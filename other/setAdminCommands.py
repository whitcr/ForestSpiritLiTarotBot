from aiogram import types
from aiogram.dispatcher.filters import IDFilter
from bot import dp, bot, cursor, db
from constants import ADMIN_ID
from aiogram import types
from aiogram.types import ContentType, Message
from aiogram.utils.markdown import hlink
from datetime import datetime
import pytz
import pendulum
import keyboard as kb
import datetime
from datetime import timedelta
from datetime import datetime
from aiogram.dispatcher.filters import IDFilter

CHAT_ID = -1001894916266


@dp.message_handler(IDFilter(chat_id = CHAT_ID), commands = ['размут', 'unmute'], commands_prefix = '!',
                    is_chat_admin = True)
async def unmute(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на сообщение!")
        return
    try:
        name = message.reply_to_message.from_user.full_name
        user_id = message.reply_to_message.from_user.id
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                       can_send_messages = True,
                                       can_send_media_messages = True,
                                       can_send_other_messages = True,
                                       can_add_web_page_previews = True)
        await bot.send_message(message.chat.id, f'[{name}]  разблокирован.')
    except:
        await message.reply("Попробуй !размут.")


@dp.message_handler(IDFilter(chat_id = CHAT_ID), commands = ['разбaн', 'unban'], commands_prefix = '!',
                    is_chat_admin = True)
async def unban(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на сообщение!")
        return
    try:
        name = message.reply_to_message.from_user.full_name
        user_id = message.reply_to_message.from_user.id
        await bot.unban_chat_member(message.chat.id, user_id)
        await bot.send_message(message.chat.id, f'[{name} разблокирован.')
    except:
        await message.reply("Попробуй !разбан.")


@dp.message_handler(IDFilter(chat_id = CHAT_ID), commands = ['мут', 'mute'], commands_prefix = '!',
                    is_chat_admin = True)
async def mute(message):
    try:
        name1 = message.from_user.get_mention(as_html = True)
        if not message.reply_to_message:
            await message.reply("Эта команда должна быть ответом на сообщение!")
            return
        try:
            muteint = int(message.text.split()[1])
            mutetype = message.text.split()[2]
            comment = " ".join(message.text.split()[3:])
        except IndexError:
            await message.reply('Не хватает аргументов!\nПример:\n`!мут 1 ч причина`')
            return
        if mutetype == "ч" or mutetype == "часов" or mutetype == "час":
            dt = datetime.now() + timedelta(hours = muteint)
            timestamp = dt.timestamp()
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                           types.ChatPermissions(False), until_date = timestamp)
            await message.reply(
                f' <b>Нарушитель:</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">'
                f'{message.reply_to_message.from_user.first_name}</a>\n<b>Срок наказания:</b> {muteint}'
                f' {mutetype}\n<b>Причина:</b> {comment}',
                parse_mode = 'html')
        elif mutetype == "м" or mutetype == "минут" or mutetype == "минуты":
            dt = datetime.now() + timedelta(minutes = muteint)
            timestamp = dt.timestamp()
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                           types.ChatPermissions(False), until_date = timestamp)
            await message.reply(
                f' <b>Нарушитель:</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">'
                f'{message.reply_to_message.from_user.first_name}</a>\n<b>Срок наказания:</b> {muteint}'
                f' {mutetype}\n<b>Причина:</b> {comment}',
                parse_mode = 'html')
        elif mutetype == "д" or mutetype == "дней" or mutetype == "день":
            dt = datetime.now() + timedelta(days = muteint)
            timestamp = dt.timestamp()
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                           types.ChatPermissions(False), until_date = timestamp)
            await message.reply(
                f' <b>Нарушитель:</b> <a href="tg://user?id={message.reply_to_message.from_user.id}">'
                f'{message.reply_to_message.from_user.first_name}</a>\n<b>Срок наказания:</b> {muteint}'
                f' {mutetype}\n<b>Причина:</b> {comment}',
                parse_mode = 'html')
    except:
        pass


# @dp.message_handler(lambda message: message.text.lower() == "установить правила", is_chat_admin=True)
# async def set_rules(message: types.Message):
#     await message.answer(f'Отправьте текст правил чата.')
#     await Set.rules.set()
#
# @dp.message_handler(state=Set.rules)
# async def meaning_choose(message: types.Message, state: FSMContext):
#     await state.update_data(rules=message.text)
#     data = await state.get_data()
#     rules = str(data['rules'])
#     chat_id = message.chat.id
#     try:
#         try:
#             cursor.execute("select rules from chats where chat_id = {};".format(chat_id))
#             rules_exist = cursor.fetchone()[0]
#             cursor.execute("UPDATE chats SET rules = '{}' where chat_id = {};".format(rules, chat_id))
#         except:
#             cursor.execute("insert into chats (chat_id, rules) values ({}, '{}')".format(chat_id, rules))
#         await message.answer(f'Сделано!')
#     except:
#         await message.answer(f'Что-то пошло не так. ')
#     await state.finish()
#     db.commit()

@dp.message_handler(IDFilter(chat_id = CHAT_ID), commands = ['warn', 'варн'], commands_prefix = '!',
                    is_chat_admin = True)
async def warnUser(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        try:
            if not message.reply_to_message:
                await message.reply("Отправь эту команду ответом на сообщение нарушителя.")
            else:
                user_id = message.reply_to_message.from_user.id
                username = message.reply_to_message.from_user.full_name
                cursor.execute("SELECT warns FROM users_chat WHERE user_id = {};".format(user_id))
                data = cursor.fetchone()
                if data is None:
                    cursor.execute("INSERT INTO users_chat(warns, user_id) VALUES({}, {});".format(1, user_id))
                    await message.reply(f"Количество варнов у {username}: 1")
                elif data[0] < 3:
                    warn = data[0] + 1
                    if warn < 3:
                        cursor.execute("UPDATE users_chat SET warns = {} where user_id = {}".format(warn, user_id))
                        await message.reply(f"Количество варнов у {username}: {warn}")
                    elif warn == 3:
                        try:
                            cursor.execute("delete from users_chat where warns = 2;")
                            await bot.kick_chat_member(chat_id = message.chat.id, user_id = user_id)
                            await message.reply("Пока, дружок.")
                        except:
                            await message.reply(f"{username} хоть и подонок, но исключить нельзя.")
                else:
                    pass
                db.commit()
        except TypeError:
            pass
    else:
        return 0


@dp.message_handler(IDFilter(chat_id = CHAT_ID), lambda message: message.text.lower().endswith("!снять варн"),
                    is_chat_admin = True)
async def unwarnUser(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        if not message.reply_to_message:
            await message.answer("Отправь эту команду ответом на сообщение нарушителя.")
        else:
            try:
                user_id = message.reply_to_message.from_user.id
                username = message.reply_to_message.from_user.full_name
                chat_id = message.reply_to_message.chat.id
                cursor.execute("SELECT warns FROM users_chat WHERE user_id = {};".format(user_id))
                data = cursor.fetchone()
                if data is None:
                    await message.reply(f"У {username} нет варнов")
                elif data[0] < 3:
                    warn = data[0] - 1
                    cursor.execute("UPDATE users_chat SET warns = {} where user_id = {};".format(user_id, chat_id))
                    await message.reply(f"Количество варнов у {username}: {warn}")
                else:
                    pass
                db.commit()
            except:
                pass
    else:
        return 0


@dp.message_handler(IDFilter(chat_id = CHAT_ID), commands = ['ban', 'бан'], commands_prefix = '!', is_chat_admin = True)
async def ban(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        if not message.reply_to_message:
            await message.reply("Отправь эту команду ответом на сообщение нарушителя.")
        else:
            try:
                replied_user = message.reply_to_message.from_user.id
                name_user = message.reply_to_message.from_user.first_name
                await bot.kick_chat_member(chat_id = message.chat.id, user_id = replied_user)
                await bot.delete_message(chat_id = message.chat.id, message_id = message.message_id)
                await bot.send_message(chat_id = message.chat.id, text = f"Дружок {name_user} забанен, радуемся.")
            except:
                await message.reply(f"{name_user} хоть и подонок, но исключить нельзя.")
    else:
        pass


@dp.message_handler(IDFilter(chat_id = CHAT_ID), commands = ['тест'], commands_prefix = '!', is_chat_admin = True)
async def ban(message: types.Message):
    print(message)
