from main import dp, bot
from constants import ADMIN_ID
from aiogram import types, Router
from aiogram.utils.markdown import hlink
from datetime import datetime
import pytz
import pendulum
import keyboard as kb
from aiogram.types import InlineKeyboardMarkup,\
    InlineKeyboardButton

router = Router()


@router.message(commands = ['старт', 'start'], commands_prefix = '!/')
async def start(message: types.Message):
    command_params = message.text

    if "ref_" in command_params:
        referrer_id = command_params.split("_")[-1]
        user_id = message.from_user.id

        if str(user_id) == referrer_id:
            await bot.send_message(user_id, f"Пригласил сам себя? Умно, но.. нет!")
            return

        cursor.execute("SELECT user_id FROM users_contest WHERE user_id = %s", (str(user_id),))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("SELECT invited FROM users_contest WHERE user_id = %s", (str(referrer_id),))
            invited = cursor.fetchone()[0]
            invited = invited if invited else []  # Fetch the current invited list or initialize as an empty list
            if int(user_id) not in invited:  # Check if the user is not already in the invited list
                invited.append(int(user_id))  # Add the user to the invited list
                cursor.execute("UPDATE users_contest SET invited = %s WHERE user_id = %s", (invited, str(referrer_id)))
                db.commit()

                if len(invited) < 3:
                    await bot.send_message(referrer_id,
                                           f"Ты пригласил друга, спасибо! За троих приглашенных тебя ждет подарок!")
                elif len(invited) == 3:
                    user_button = InlineKeyboardButton(text = "Проверить и получить приз!",
                                                       callback_data = "check_invited")
                    check_invited_keyboard = InlineKeyboardMarkup(resize_keyboard = True).add(user_button)

                    await bot.send_message(referrer_id,
                                           f"Ты пригласил трех друзей, спасибо! Давай проверим, подписаны ли все твои приглашенные друзья на каналы и отправим тебе подарок!",
                                           reply_markup = check_invited_keyboard)

                else:
                    pass

                await bot.send_message(user_id,
                                       'Тебя пригласил друг, рады видеть. Если хочешь участвовать в конкурсе, подпишись на эти каналы:',
                                       reply_markup = kb.follow_contest_keyboard)
        else:
            await bot.send_message(user_id, "Тебя пригласили, но ты уже участвуешь в конкурсе!")
            await bot.send_message(referrer_id,
                                   f"Приглашенный тобой друг уже участвует в конкурсе!")
        return

    if message.chat.type == "private":
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.reply(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?',
                            reply_markup = kb.menu_private_keyboard)
    else:
        await get_help(message)


@router.message(commands = ['menu', 'меню'], commands_prefix = '!/')
async def get_help(message: types.Message):
    if message.chat.type == "private":
        await message.reply(f'Вот тебе меню!',
                            reply_markup = kb.menu_private_keyboard)


@router.message(lambda message: message.text.lower() == "помощь")
async def get_help(message: types.Message):
    if message.chat.type == "private":
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.answer(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?',
                             reply_markup = kb.menu_private_keyboard)
    else:
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.answer(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?')


# @dp.message_handler(content_types = [ContentType.NEW_CHAT_MEMBERS])
# async def new_members_handler(message: Message):
#     chat_id = message.chat.id
#     new_member = message.new_chat_members[0].first_name
#     id = message.new_chat_members[0].id
#     try:
#         if id == BOT_ID:
#             text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
#             await bot.send_message(message.chat.id,
#                                    f"{text} Приветствую. В статье вы сможете ознакомиться с правилами и инструкциями.")
#         # else:
#         #     cursor.execute("select rules from chats where chat_id = {};".format(chat_id))
#         #     rules = cursor.fetchone()[0]
#         #     await bot.send_message(message.chat.id, f"Добро пожаловать, <b>{new_member}.</b>\n\n"
#         #                                             f"{rules}")
#     except:
#         await bot.send_message(message.chat.id, f"Добро пожаловать, <b>{new_member}.</b>")


# @dp.message_handler(lambda message: message.text.lower() == "правила")
# async def set_rules(message: types.Message):
#     chat_id = message.chat.id
#     try:
#         cursor.execute("select rules from chats where chat_id = {};".format(chat_id))
#         rules = cursor.fetchone()[0]
#         await bot.send_message(chat_id, f"{rules}")
#     except:
#         await bot.send_message(chat_id, f"У вас нет правил, позорники!")


@dp.message_handler(lambda message: message.text.lower() == "заказать расклад")
async def uslugi(message: types.Message):
    if message.chat.type == 'private':
        link = f"https://t.me/forestspiritoo"
        group = hlink("группе", link)
        link = f"https://t.me/forestspiritoo"
        wanderer = hlink("Страннику", link)
        link = f"https://t.me/forestspiritoo/54"
        love_spread = hlink("Все о любви, его чувствах и намерениях", link)
        link = f"https://t.me/forestspiritoo/56"
        self_spread = hlink("Понимая себя, мы открываем совершенно иной мир", link)
        link = f"https://t.me/forestspiritoo/57"
        money_spread = hlink("Как улучшть свои финансы и что принесет мне этот путь?", link)
        link = f"https://t.me/forestspiritoo/59?comment=39"
        animal_spread = hlink("Узнать своих тотемных животных и облегчить свою жизнь", link)
        link = f"https://t.me/forestspiritoo/59?comment=38"
        energy_spread = hlink("Диагностика энергополя и чакр", link)
        await bot.send_message(message.chat.id,
                               text = f"— Вы можете ознакомиться с раскладами и иными услугами в этой {group} или напрямую обратиться "
                                      f"к {wanderer}\n\n"
                                      f"<b>ПОПУЛЯРНЫЕ РАСКЛАДЫ:</b>\n\n"
                                      f"{love_spread}\n\n"
                                      f"{self_spread}\n\n"
                                      f"{money_spread}\n\n"
                                      f"<b>ВАЖНЫЕ ДИАГНОСТИКИ: </b>\n\n"
                                      f"{animal_spread}\n\n"
                                      f"{energy_spread}\n\n")
    else:
        pass


@dp.message_handler(lambda message: message.text.lower().endswith("библиотека"))
async def uslugi(message: types.Message):
    if message.chat.type == 'private':
        link = hlink('библиотеку', 'https://t.me/forestlibraryspirit')
        await bot.send_message(message.chat.id, text = f"— Приглашаем тебя в нашу {link}.")
    else:
        pass


@dp.message_handler(lambda message: message.text.lower() == "удалить расклад дня")
async def delete_day_spread(message: types.Message):
    user_id = message.from_user.id
    newdate = datetime.now(pytz.timezone('Europe/Kiev'))
    date = newdate.strftime("%d.%m")
    cursor.execute("delete FROM spreads_day WHERE user_id = '{}' and date = '{}'".format(user_id, date))
    await message.reply("Ваш расклад дня удален, но даже не найдетесь, что он не проиграется.")


@dp.message_handler(lambda message: message.text.lower() == "удалить расклад на завтра")
async def delete_tomorrow_spread(message: types.Message):
    user_id = message.from_user.id
    tomorrow = pendulum.tomorrow('Europe/Kiev').format('DD.MM')
    cursor.execute("delete FROM spreads_day WHERE user_id = '{}' and date = '{}'".format(user_id, tomorrow))
    await message.reply("Ваш расклад на завтра удален, но даже не найдетесь, что он не проиграется.")


@dp.message_handler(lambda message: message.text.lower() == "!айди")
async def test(message: types.Message):
    await bot.send_message(ADMIN_ID, f"{message.from_user.id}")
