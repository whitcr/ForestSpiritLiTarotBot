from aiogram import types, Router, F

from database import execute_select_all
from main import bot
import keyboard as kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == 'practice_menu_meditation')
async def practice_zalivka_answer(call: types.CallbackQuery):
    try:
        await call.answer()

        meditations = execute_select_all("SELECT text, name FROM meditation_text")

        keyboard = InlineKeyboardMarkup()
        button_right = InlineKeyboardButton('Больше медитаций!', callback_data = f'show_meditations_{1}')
        keyboard.add(button_right)

        current_meditation_index = 0
        current_meditation = meditations[current_meditation_index]

        title = current_meditation[1]
        description = current_meditation[0]

        meditation_message = f"<b>{title}:</b>\n\n{description}"
        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = meditation_message,
                                    reply_markup = keyboard)
    except Exception:
        pass


@router.callback_query(F.data.startswith('show_meditations'))
async def process_callback_show_meditations(call: types.CallbackQuery):
    try:
        await call.answer()
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            meditations = execute_select_all("SELECT text, name FROM meditation_text")
            index = int(call.data.split('_')[2])
            current_meditation = meditations[index]
            title = current_meditation[1]
            description = current_meditation[0]

            meditation_message = f"<b>{title}:</b>\n\n{description}"

            keyboard = InlineKeyboardMarkup(row_width = 2)
            if len(meditations) == 1:
                pass
            elif index == 0:
                button_right = InlineKeyboardButton('-->', callback_data = f'show_meditations_{index + 1}')
                button_last = InlineKeyboardButton('<--', callback_data = f'show_meditations_{len(meditations) - 1}')
                keyboard.row(button_last, button_right)
            elif index == len(meditations) - 1:
                button_first = InlineKeyboardButton('-->', callback_data = f'show_meditations_0')
                button_left = InlineKeyboardButton('<--', callback_data = f'show_meditations_{index - 1}')
                keyboard.row(button_left, button_first)
            else:
                button_left = InlineKeyboardButton('<--', callback_data = f'show_meditations_{index - 1}')
                button_right = InlineKeyboardButton('-->', callback_data = f'show_meditations_{index + 1}')
                keyboard.row(button_left, button_right)

            await bot.edit_message_text(chat_id = call.message.chat.id,
                                        message_id = call.message.message_id,
                                        text = meditation_message,
                                        reply_markup = keyboard)
    except Exception:
        pass


@router.callback_query(F.data == 'practice_menu_practice')
async def practice_practices(call: types.CallbackQuery):
    await call.answer()
    try:
        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = f"Выберите тематику практик.",
                                    reply_markup = kb.practice_general_menu_practices_keyboard)
    except:
        return 0


@router.callback_query(F.data.startswith('practices_'))
async def process_callback_practices(call: types.CallbackQuery):
    try:
        await call.answer()
        keyword = call.data.split('_')[1]
        practices = execute_select_all("SELECT name,text FROM practices_text WHERE keyword LIKE %s",
                                       ('%' + keyword + '%',))

        keyboard = InlineKeyboardMarkup()
        button_right = InlineKeyboardButton('Больше практик!', callback_data = f'show_practice_{1}_{keyword}')
        keyboard.add(button_right)

        current_practices_index = 0
        current_practices = practices[current_practices_index]
        title = current_practices[0]
        description = current_practices[1]

        practice_message = f"<b>{title}:</b>\n\n{description}"

        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = practice_message,
                                    reply_markup = keyboard)
    except Exception:
        pass


@router.callback_query(F.data.startswith('show_practice'))
async def process_callback_show_practice(call: types.CallbackQuery):
    await call.answer()
    try:
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            index = int(call.data.split('_')[2])
            keyword = call.data.split('_')[3]
            practices = execute_select_all("SELECT name, text FROM practices_text WHERE keyword LIKE %s",
                                           ('%' + keyword + '%',))

            current_practice = practices[index]
            title = current_practice[0]
            description = current_practice[1]
            practice_message = f"<b>{title}:</b>\n\n{description}"

            keyboard = InlineKeyboardMarkup(row_width = 2)
            if len(practices) == 1:
                pass
            elif index == 0:
                button_right = InlineKeyboardButton('-->', callback_data = f'show_practice_{index + 1}_{keyword}')
                button_last = InlineKeyboardButton('<--',
                                                   callback_data = f'show_practice_{len(practices) - 1}_{keyword}')
                keyboard.row(button_last, button_right)
            elif index == len(practices) - 1:
                button_first = InlineKeyboardButton('-->', callback_data = f'show_practice_0_{keyword}')
                button_left = InlineKeyboardButton('<--', callback_data = f'show_practice_{index - 1}_{keyword}')
                keyboard.row(button_left, button_first)
            else:
                button_left = InlineKeyboardButton('<--', callback_data = f'show_practice_{index - 1}_{keyword}')
                button_right = InlineKeyboardButton('-->', callback_data = f'show_practice_{index + 1}_{keyword}')
                keyboard.row(button_left, button_right)

            await bot.edit_message_text(chat_id = call.message.chat.id,
                                        message_id = call.message.message_id,
                                        text = practice_message,
                                        reply_markup = keyboard)
    except Exception:
        pass
