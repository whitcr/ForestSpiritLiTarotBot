# from main import dp, bot
# from aiogram import types
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
#
# from aiogram.types import InputFile
#
# BOOK_CHANNEL_ID = -1001607817353
#
#
# class saveBooks(StatesGroup):
#     save = State()
#
#
# async def split_description(message: types.Message):
#     description = message.caption.split('#')[0].strip()
#     new_name = message.caption.split('#')[1]
#     keywords = [kw.strip() for kw in message.caption.split('#')[2:] if kw.strip()]
#     return description, new_name, keywords
#
#
# @dp.message_handler(lambda message: message.text.startswith("+книга"))
# async def get_save_book(message: types.Message):
#     await message.reply(f'Кинь книгу в формате: описание #название #хештег#хештег.')
#     await saveBooks.save.set()
#
#
# @dp.message_handler(content_types = ['document'], state = saveBooks.save)
# async def save_book(message: types.Message, state: saveBooks.save):
#     await message.reply(f'Сохраняю.')
#     book_id = message.document.file_id
#     description, new_name, keywords = await split_description(message)
#
#     msg = await bot.send_document(BOOK_CHANNEL_ID, document = book_id, caption = description)
#     file_id = msg.document.file_id
#
#     cursor.execute("INSERT INTO library (title, description, keywords, book_id) VALUES (%s, %s, %s, %s) ",
#                    (new_name, description, keywords, file_id))
#     await state.finish()
#     db.commit()
#
#
# @dp.message_handler(lambda message: message.text.lower().startswith("книга"))
# async def find_books(message: types.Message):
#     if len(message.text.split(' ')) == 1:
#
#         random_button = InlineKeyboardButton(text = f"Случайный выбор",
#                                              callback_data = f"show_random_book")
#         keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 1).add(
#             random_button)
#
#         cursor.execute(f"SELECT keywords FROM library GROUP BY keywords ORDER BY RANDOM() LIMIT 1")
#
#         examples = cursor.fetchall()
#         examples = examples[0][0].replace(',', ', ').replace('{', '').replace('}', '')
#         await message.reply(f'Выберите тематику запроса. К примеру: книга {examples} ', reply_markup = keyboard)
#     else:
#         keyword = message.text.split(' ')[1]
#         cursor.execute("SELECT title, description, book_id FROM library WHERE keywords LIKE %s", ('%' + keyword + '%',))
#         books = cursor.fetchall()
#         if len(books) == 0:
#             await message.reply(f'Прости, ничего не найдено по запросу: {keyword}.')
#         else:
#             keyboard = InlineKeyboardMarkup()
#             button_right = InlineKeyboardButton('Искать книги', callback_data = f'show_book_{1}')
#             keyboard.add(button_right)
#
#             current_book_index = 0
#             current_book = books[current_book_index]
#             title = current_book[0]
#             description = current_book[1]
#             book_id = current_book[2]
#             book_message = f"<b>{title}:</b>\n\n{description}"
#
#             await bot.send_document(chat_id = message.chat.id,
#                                     caption = book_message,
#                                     document = book_id,
#                                     reply_markup = keyboard,
#                                     reply_to_message_id = message.message_id)
#
#
# @dp.callback_query_handler(lambda c: c.data.startswith('show_book'))
# async def process_callback_show_book(call: types.CallbackQuery):
#     await call.answer()
#     if call.from_user.id == call.message.reply_to_message.from_user.id:
#         index = int(call.data.split('_')[2])
#         keyword = call.message.reply_to_message.text.split(' ')[1:]
#         cursor.execute("SELECT title, description, book_id FROM library WHERE keywords LIKE %s",
#                        ('%' + keyword[0] + '%',))
#         books = cursor.fetchall()
#         current_book = books[index]
#         title = current_book[0]
#         description = current_book[1]
#         book_id = current_book[2]
#         book_message = f"<b>{title}:</b>\n\n{description}"
#
#         keyboard = InlineKeyboardMarkup(row_width = 2)
#         if len(books) == 1:
#             pass
#         elif index == 0:
#             button_right = InlineKeyboardButton('-->', callback_data = f'show_book_{index + 1}')
#             button_last = InlineKeyboardButton('<--', callback_data = f'show_book_{len(books) - 1}')
#             keyboard.row(button_last, button_right)
#         elif index == len(books) - 1:
#             button_first = InlineKeyboardButton('-->', callback_data = f'show_book_0')
#             button_left = InlineKeyboardButton('<--', callback_data = f'show_book_{index - 1}')
#             keyboard.row(button_left, button_first)
#         else:
#             button_left = InlineKeyboardButton('<--', callback_data = f'show_book_{index - 1}')
#             button_right = InlineKeyboardButton('-->', callback_data = f'show_book_{index + 1}')
#             keyboard.row(button_left, button_right)
#
#         media = types.InputMediaDocument(media = book_id, caption = book_message)
#
#         await bot.edit_message_media(chat_id = call.message.chat.id,
#                                      message_id = call.message.message_id,
#                                      media = media,
#                                      reply_markup = keyboard)
#
#
# @dp.callback_query_handler(lambda c: c.data.startswith('show_random_book'))
# async def process_callback_show_random_book(call: types.CallbackQuery):
#     await call.answer()
#     if call.from_user.id == call.message.reply_to_message.from_user.id:
#         cursor.execute("SELECT title, description, book_id FROM library ORDER BY RANDOM() LIMIT 1")
#         current_book = cursor.fetchall()[0]
#         title = current_book[0]
#         description = current_book[1]
#         book_id = current_book[2]
#         book_message = f"<b>{title}:</b>\n\n{description}"
#
#         await bot.send_document(chat_id = call.message.chat.id,
#                                 caption = book_message,
#                                 document = book_id,
#                                 reply_to_message_id = call.message.reply_to_message.message_id)
