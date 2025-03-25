from aiogram import types, Router, F, Bot
from database import execute_select_all
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from filters.baseFilters import IsReply
from middlewares.statsUser import use_user_statistics

router = Router()


@router.callback_query(IsReply(), F.data == 'practice_menu_meditation')
async def practice_zalivka_answer(bot: Bot, call: types.CallbackQuery):
    try:
        await call.answer()

        meditations = await execute_select_all("SELECT text, name FROM meditation_text")

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


@router.callback_query(IsReply(), F.data.startswith('show_meditations'))
async def process_callback_show_meditations(bot: Bot, call: types.CallbackQuery):
    try:
        await call.answer()
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            meditations = await execute_select_all("SELECT text, name FROM meditation_text")
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
