from aiogram import types, Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import execute_select_all
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from filters.baseFilters import IsReply
from middlewares.statsUser import use_user_statistics

router = Router()


@router.callback_query(IsReply(), F.data == 'practice_menu_meditation')
async def practice_zalivka_answer(call: types.CallbackQuery, bot: Bot):
    try:
        await call.answer()

        meditations = await execute_select_all("SELECT text, name FROM meditation_text")

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text = 'Больше медитаций!', callback_data = f'show_meditations_{1}')

        current_meditation_index = 0
        current_meditation = meditations[current_meditation_index]

        title = current_meditation[1]
        description = current_meditation[0]

        meditation_message = f"<b>{title}:</b>\n\n{description}"
        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = meditation_message,
                                    reply_markup = keyboard.as_markup())
    except Exception:
        pass


@router.callback_query(IsReply(), F.data.startswith('show_meditations'))
async def process_callback_show_meditations(call: types.CallbackQuery, bot: Bot):
    try:
        await call.answer()
        meditations = await execute_select_all("SELECT text, name FROM meditation_text")
        index = int(call.data.split('_')[2])
        current_meditation = meditations[index]
        title = current_meditation[1]
        description = current_meditation[0]

        meditation_message = f"<b>{title}:</b>\n\n{description}"

        keyboard = InlineKeyboardBuilder()

        if len(meditations) == 1:
            pass
        elif index == 0:
            keyboard.button(text = '<--', callback_data = f'show_meditations_{len(meditations) - 1}')
            keyboard.button(text = '-->', callback_data = f'show_meditations_{index + 1}')
        elif index == len(meditations) - 1:
            keyboard.button(text = '<--', callback_data = f'show_meditations_{index - 1}')
            keyboard.button(text = '-->', callback_data = f'show_meditations_0')
        else:
            keyboard.button(text = '-->', callback_data = f'show_meditations_{index + 1}')
            keyboard.button(text = '<--', callback_data = f'show_meditations_{index - 1}')

        keyboard.button(text = 'Меню', callback_data = f'get_practices_menu')
        keyboard.adjust(2)

        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = meditation_message,
                                    reply_markup = keyboard.as_markup())
    except Exception:
        pass
