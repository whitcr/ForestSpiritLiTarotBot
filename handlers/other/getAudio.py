from aiogram import types
from bot import dp, bot, cursor
from random import randint
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

AUDIO_MAP = {
    'медитация': 'meditations',
    'мантра': 'mantras',
    'саб': 'sabliminals',
}


@dp.message_handler(lambda message: message.text.lower().startswith(tuple(AUDIO_MAP.keys())))
async def find_meditation(message: types.Message):
    words = message.text.split()
    theme = AUDIO_MAP[words[0].lower()]
    table_name = "audio_" + theme
    if len(words) == 1:

        random_button = InlineKeyboardButton(text = f"Случайный выбор",
                                             callback_data = f"show_random_audio_{theme}")
        keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 1).add(
            random_button)

        cursor.execute(f"SELECT keywords FROM {table_name} GROUP BY keywords ORDER BY RANDOM() LIMIT 1")

        examples = cursor.fetchall()
        examples = examples[0][0].replace(',', ', ')
        await message.reply(f'Выберите тематику запроса. К примеру: {words[0]} {examples} ', reply_markup = keyboard)
    else:
        keyword = message.text.split(' ')[1]
        cursor.execute(f"SELECT file_id FROM {table_name}  WHERE keywords LIKE %s", ('%' + keyword + '%',))
        audio = cursor.fetchall()

        if len(audio) == 0:
            await message.reply(f'Прости, ничего не найдено по запросу: {keyword}.')
        else:
            keyboard = InlineKeyboardMarkup()
            button_right = InlineKeyboardButton('Искать еще!', callback_data = f'show_audio_{theme}_{1}')
            keyboard.add(button_right)

            current_audio_index = 0
            current_audio = audio[current_audio_index]
            audio_id = current_audio[0]

            await bot.send_audio(chat_id = message.chat.id,
                                 audio = audio_id,
                                 reply_markup = keyboard,
                                 reply_to_message_id = message.message_id)


@dp.callback_query_handler(lambda c: c.data.startswith('show_audio'))
async def process_callback_show_audio(call: types.CallbackQuery):
    await call.answer()
    try:
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            index = int(call.data.split('_')[3])
            theme = call.data.split('_')[2]
            table_name = "audio_" + theme
            keyword = call.message.reply_to_message.text.split(' ')[1:]
            cursor.execute(f"SELECT file_id FROM  {table_name}  WHERE keywords LIKE %s", ('%' + keyword[0] + '%',))
            audio = cursor.fetchall()
            current_audio = audio[index]
            audio_id = current_audio[0]

            keyboard = InlineKeyboardMarkup(row_width = 2)
            if len(audio) == 1:
                pass
            elif index == 0:
                button_right = InlineKeyboardButton('-->', callback_data = f'show_audio_{theme}_{index + 1}')
                button_last = InlineKeyboardButton('<--', callback_data = f'show_audio_{theme}_{len(audio) - 1}')
                keyboard.row(button_last, button_right)
            elif index == len(audio) - 1:
                button_first = InlineKeyboardButton('-->', callback_data = f'show_audio_{theme}_0')
                button_left = InlineKeyboardButton('<--', callback_data = f'show_audio_{theme}_{index - 1}')
                keyboard.row(button_left, button_first)
            else:
                button_left = InlineKeyboardButton('<--', callback_data = f'show_audio_{theme}_{index - 1}')
                button_right = InlineKeyboardButton('-->', callback_data = f'show_audio_{theme}_{index + 1}')
                keyboard.row(button_left, button_right)

            await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)
            await bot.send_audio(chat_id = call.message.chat.id,
                                 audio = audio_id,
                                 reply_markup = keyboard,
                                 reply_to_message_id = call.message.reply_to_message.message_id)
    except:
        pass



@dp.callback_query_handler(lambda c: c.data.startswith('show_random_audio'))
async def process_callback_show_random_audio(call: types.CallbackQuery):
    await call.answer()
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        theme = call.data.split('_')[3]
        table_name = "audio_" + theme
        cursor.execute(f"SELECT file_id FROM {table_name} ORDER BY RANDOM() LIMIT 1")
        audio_id = cursor.fetchone()[0]
        await bot.send_audio(chat_id = call.message.chat.id,
                             audio = audio_id)
