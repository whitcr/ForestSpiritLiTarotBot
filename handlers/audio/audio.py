from aiogram import types, Bot, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import execute_select_all, execute_select
from filters.baseFilters import IsReply
from filters.subscriptions import SubscriptionLevel
from middlewares.statsUser import use_user_statistics

AUDIO_MAP = {
    'медитация': 'meditations',
    'мантра': 'mantras',
    'саб': 'sabliminals',
}

router = Router()


@router.message(F.text.lower().startswith(tuple(AUDIO_MAP.keys())), SubscriptionLevel(2))
@use_user_statistics
async def find_meditation(bot: Bot, message: types.Message):
    words = message.text.split()
    theme = AUDIO_MAP[words[0].lower()]
    table_name = "audio_" + theme

    if len(words) == 1:
        random_button = InlineKeyboardButton(
            text = "Случайный выбор",
            callback_data = f"show_random_audio_{theme}"
        )
        keyboard = InlineKeyboardBuilder().add(random_button).as_markup()

        examples = await execute_select_all(
            f"SELECT keywords FROM {table_name} GROUP BY keywords ORDER BY RANDOM() LIMIT 1"
        )

        examples = examples[0][0].replace(',', ', ')
        await message.reply(f'Выберите тематику запроса. К примеру: {words[0]} {examples} ', reply_markup = keyboard)
    else:
        keyword = message.text.split(' ')[1]
        audio = await execute_select_all(
            f"SELECT file_id FROM {table_name} WHERE keywords LIKE $1",
            ('%' + keyword + '%',)
        )

        if len(audio) == 0:
            await message.reply(f'Прости, ничего не найдено по запросу: {keyword}.')
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard = [
                    [InlineKeyboardButton('Искать еще!', callback_data = f'show_audio_{theme}_{1}')]
                ]
            )

            current_audio = audio[0]
            audio_id = current_audio[0]

            await bot.send_audio(chat_id = message.chat.id,
                                 audio = audio_id,
                                 reply_markup = keyboard,
                                 reply_to_message_id = message.message_id)


@router.callback_query(IsReply(), F.data.startswith('show_audio'))
@use_user_statistics
async def process_callback_show_audio(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    try:
        data_parts = call.data.split('_')
        index = int(data_parts[3])
        theme = data_parts[2]
        table_name = "audio_" + theme
        keyword = call.message.reply_to_message.text.split(' ')[1:]
        audio = await execute_select_all(f"SELECT file_id FROM {table_name} WHERE keywords LIKE $1",
                                         ('%' + keyword[0] + '%',))

        current_audio = audio[index]
        audio_id = current_audio[0]

        keyboard = InlineKeyboardBuilder()
        if len(audio) > 1:
            if index == 0:
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
                             reply_markup = keyboard.as_markup(),
                             reply_to_message_id = call.message.reply_to_message.message_id)
    except Exception as e:
        raise Exception


@router.callback_query(IsReply(), F.data.startswith('show_random_audio'))
@use_user_statistics
async def process_callback_show_random_audio(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    theme = call.data.split('_')[3]
    table_name = "audio_" + theme
    audio_id = await execute_select(f"SELECT file_id FROM {table_name} ORDER BY RANDOM() LIMIT 1")
    await bot.send_audio(chat_id = call.message.chat.id,
                         audio = audio_id)
