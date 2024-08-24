# from main import dp, bot
#
# from aiogram import types
# from aiogram.dispatcher.filters import IDFilter
# import re
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from constants import CARDS_NAME_SYNONYMS, CARDS, CHAT_ID
# import asyncio
#
# CARDS = set(CARDS)
#
#
# # CHAT_ID = -1001928497656
#
# async def replace_synonyms(text):
#     words = text.lower().split()
#     for i, word in enumerate(words):
#         for key, synonyms_list in CARDS_NAME_SYNONYMS.items():
#             if word in synonyms_list:
#                 words[i] = key
#     name = " ".join(words)
#     text = text.lower()
#     for i in enumerate(text):
#         for key, synonyms_list in CARDS_NAME_SYNONYMS.items():
#             if text in synonyms_list:
#                 name = key
#     return name
#
#
# async def generate_keyboard(user_id):
#     buttons = [
#         InlineKeyboardButton(text = "Сохранить", callback_data = f"chat_meaning_save_{user_id}"),
#         InlineKeyboardButton(text = "Ситуация", callback_data = f"chat_meaning_savesituation_{user_id}"),
#         InlineKeyboardButton(text = "Варн", callback_data = f"chat_meaning_warn_{user_id}"),
#         InlineKeyboardButton(text = "Удалить", callback_data = f"chat_meaning_delete_{user_id}"),
#     ]
#
#     keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 2)
#     keyboard.add(*buttons)
#
#     return keyboard
#
#
# @dp.callback_query_handler(lambda call: call.data.startswith('chat_meaning_'))
# async def meaning_cb(call: types.CallbackQuery):
#     await call.answer()
#     chat_member = await bot.get_chat_member(chat_id = CHAT_ID, user_id = call.from_user.id)
#     if chat_member.status in [types.ChatMemberStatus.ADMINISTRATOR, types.ChatMemberStatus.CREATOR]:
#         call_type = call.data.split('_')[2]
#         user_id = call.data.split('_')[3]
#         text = call.message.reply_to_message.text
#         if text is None:
#             text = call.message.reply_to_message.caption
#         if call_type == "warn":
#             text_warn = f"<a href = 'tg://user?id={user_id}'>Вам</a>"
#             cursor.execute("SELECT warns FROM users_chat WHERE user_id = {};".format(user_id))
#             data = cursor.fetchone()
#             if data is None:
#                 cursor.execute("INSERT INTO users_chat(warns, user_id) VALUES({}, {});".format(1, user_id))
#                 await bot.send_message(call.message.chat.id,
#                                        f"{text_warn} вынесли варн, перепишите трактовку по всем правилам в закрепленном сообщении",
#                                        reply_to_message_id = call.message.reply_to_message.message_id)
#             elif data[0] < 3:
#                 warn = data[0] + 1
#                 if warn < 3:
#                     cursor.execute("UPDATE users_chat SET warns = {} where user_id = {}".format(warn, user_id))
#                     await bot.send_message(call.message.chat.id,
#                                            f"{text_warn} вынесли варн, перепишите трактовку по всем правилам в закрепленном сообщении",
#                                            reply_to_message_id = call.message.reply_to_message.message_id)
#
#                 elif warn == 3:
#                     cursor.execute("delete from users_chat where warns = 2;")
#                     await bot.kick_chat_member(chat_id = call.message.chat.id, user_id = user_id)
#                     await call.answer("Пока, дружок.")
#             db.commit()
#         elif call_type == "save":
#             choice = text.split("#")[1]
#             theme = "".join(text.split("#")[2]).split(" ")[0]
#
#             elements = []
#             text = text.replace("\n\n", "\n")
#             lines = text.strip().split('\n')[1:]
#
#             for line in lines:
#                 keyword, description = line.split(':', 1)
#                 elements.append((keyword.strip(), description.strip()))
#
#             cards = []
#             meaning = []
#             for element in elements:
#                 keyword = element[0].lower()
#                 keyword = await replace_synonyms(keyword)
#                 if keyword in CARDS:
#                     cards.append(keyword + ".")
#                     meaning.append(element[1] + ".")
#                 elif keyword == "ситуация":
#                     situation = element[1]
#                 elif keyword == "общая трактовка":
#                     meaning.append(element[1] + ".")
#                 elif keyword == "вопрос":
#                     question = element[1]
#
#             cursor.execute(
#                 "INSERT INTO meaning_chat (cards, situation, meaningCards, choice, theme, question) VALUES (%s, %s, %s, %s, %s, %s)",
#                 (" ".join(cards), situation, " ".join(meaning), choice, theme, question))
#             cursor.execute("select num from meaning_chat ORDER BY num DESC LIMIT 1")
#             num = cursor.fetchone()[0]
#             db.commit()
#             await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
#                                         text = f'Сохранено. Номер трактовки — {num}.')
#
#         elif call_type == "savesituation":
#             choice = text.split("#")[1]
#             theme = "".join(text.split("#")[2]).split(" ")[0]
#
#             elements = []
#             text = text.replace("\n\n", "\n")
#             lines = text.strip().split('\n')[1:]
#
#             for line in lines:
#                 keyword, description = line.split(':', 1)
#                 elements.append((keyword.strip(), description.strip()))
#
#             cards = []
#             for element in elements:
#                 keyword = element[0].lower()
#                 keyword = await replace_synonyms(keyword)
#                 if keyword in CARDS:
#                     cards.append(keyword + ".")
#                 elif keyword == "ситуация":
#                     situation = element[1]
#                 elif keyword == "вопрос":
#                     question = element[1]
#
#             cursor.execute(
#                 "INSERT INTO meaning_chat (cards, situation, choice, theme, question) VALUES (%s, %s, %s, %s, %s)",
#                 (" ".join(cards), situation, choice, theme, question))
#             cursor.execute("select num from meaning_chat ORDER BY num DESC LIMIT 1")
#             num = cursor.fetchone()[0]
#             db.commit()
#             await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
#                                         text = f'Сохранено. Номер ситуации — {num}.')
#
#         elif call_type == "delete":
#             await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)
#             await bot.delete_message(chat_id = call.message.chat.id,
#                                      message_id = call.message.reply_to_message.message_id)
#
#
# async def check_text(message):
#     text = message.text
#     if text is None:
#         text = message.caption
#     pattern = re.compile(r'^#(\w+)\s#(\w+)')
#     words = ['ситуация', 'общая трактовка', 'вопрос']
#     if re.search(pattern, text):
#         print(1)
#         if all(word.lower() in text.lower() for word in words):
#             keyboard = await generate_keyboard(message.reply_to_message.from_user.id)
#             await message.reply(f'Жди помощи! Кнопки для администрации: ', reply_markup = keyboard)
#         else:
#             await message.reply('Напиши трактовку по заданному шаблону. Твое сообщение удалится через две минуты,'
#                                 ' успей его скопировать и отправить новое по шаблону, НЕ РЕДАКТИРУЙ САМО СООБЩЕНИЕ.')
#             await asyncio.sleep(120)
#             await bot.delete_message(chat_id = message.chat.id, message_id = message.message_id)
#
#
# @dp.message_handler(IDFilter(chat_id = CHAT_ID), lambda message: message.text.lower().startswith("!с"),
#                     is_chat_admin = True)
# async def save_meaning_others(message: types.Message):
#     try:
#         if message.reply_to_message:
#             num = message.text.split(' ')[1]
#             meaning = message.reply_to_message.text
#             cursor.execute("SELECT meaning_other FROM meaning_chat WHERE num = %s", (num,))
#             check = cursor.fetchone()[0]
#             if check is not None:
#                 meaning = f"{check}\n{meaning}"
#
#             cursor.execute("UPDATE meaning_chat SET meaning_other = %s WHERE num = %s", (meaning, num))
#
#             db.commit()
#             await message.reply(f'Cохранено!')
#         else:
#             await message.reply(f'Надо писать ответом на сообщение!')
#     except:
#         await message.reply(f'Что-то пошло не так :(')
#
#
# # @dp.message_handler(IDFilter(chat_id = CHAT_ID), lambda message: message.text.lower().startswith("!удалить"),
# #                     is_chat_admin = True)
# # async def delete_messages(message: types.Message):
# #     num = int(message.text.split(' ')[1])
# #     message_id = int(message.message_id)
# #
# #     for i in range(num):
# #         id = 800 + i
# #         try:
# #             await bot.delete_message(chat_id = message.chat.id, message_id = id)
# #         except:
# #             pass
#
# @dp.message_handler(IDFilter(chat_id = CHAT_ID),
#                     lambda message: message.text.lower() in ['+', "согл", "согласен", "согласна"])
# async def get_reputation(message: types.Message):
#     if message.reply_to_message and message.reply_to_message.forum_topic_created is None:
#         if message.reply_to_message.from_user.id != message.from_user.id:
#             user_id = message.reply_to_message.from_user.id
#             cursor.execute("SELECT rep FROM users_chat WHERE user_id = %s", (user_id,))
#             rep = cursor.fetchone()[0]
#             if rep is not None:
#                 rep = rep + 1
#             else:
#                 cursor.execute("SELECT user_id FROM users_chat WHERE user_id = %s", (user_id,))
#                 check = cursor.fetchone()[0]
#                 if check is None:
#                     cursor.execute("INSERT INTO users_chat (user_id) values (%s)", (user_id))
#                 rep = 1
#
#             cursor.execute("UPDATE users_chat SET rep = %s WHERE user_id = %s", (rep, user_id))
#             db.commit()
#             await bot.send_message(message.chat.id, text = f'Вам выразили респект. Ваша репутация: {rep}',
#                                    reply_to_message_id = message.reply_to_message.message_id)
#
#
# @dp.message_handler(IDFilter(chat_id = CHAT_ID),
#                     content_types = [types.ContentType.NEW_CHAT_MEMBERS, types.ContentType.LEFT_CHAT_MEMBER])
# async def delete_system_messages(message: types.Message):
#     await message.delete()
#
# # @dp.message_handler(lambda message: message.text.lower() == "тест")
# # async def get_id(message: types.Message):
# #     # await message.reply(f"{message}")
# #     print (message)
# #     await bot.send_message(CHAT_ID , "message", reply_to_message_id = 2334)
#
#
# # @dp.message_handler(content_types = [ContentType.NEW_CHAT_MEMBERS])
# # async def new_members_handler(message: Message):
# #     chat_id = message.chat.id
# #     new_member = message.new_chat_members[0].first_name
# #     id = message.new_chat_members[0].id
# #     try:
# #         if id == BOT_ID:
# #             text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
# #             await bot.send_message(message.chat.id,
# #                                    f"{text} Приветствую. В статье вы сможете ознакомиться с правилами и инструкциями.")
# #         # else:
# #         #     cursor.execute("select rules from chats where chat_id = {};".format(chat_id))
# #         #     rules = cursor.fetchone()[0]
# #         #     await bot.send_message(message.chat.id, f"Добро пожаловать, <b>{new_member}.</b>\n\n"
# #         #                                             f"{rules}")
# #     except:
# #         await bot.send_message(message.chat.id, f"Добро пожаловать, <b>{new_member}.</b>")
#
#
# # @dp.message_handler(lambda message: message.text.lower() == "правила")
# # async def set_rules(message: types.Message):
# #     chat_id = message.chat.id
# #     try:
# #         cursor.execute("select rules from chats where chat_id = {};".format(chat_id))
# #         rules = cursor.fetchone()[0]
# #         await bot.send_message(chat_id, f"{rules}")
# #     except:
# #         await bot.send_message(chat_id, f"У вас нет правил, позорники!")
