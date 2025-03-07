from aiogram import types, Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
import keyboard as kb
from constants import MEANINGS_BUTTONS
from database import execute_select
from functions.store.temporaryStore import get_data

router = Router()


async def generate_meaning_keyboard(user_choice, callback_data):
    meanings_button = MEANINGS_BUTTONS.get(user_choice, MEANINGS_BUTTONS.get("raider"))

    builder = InlineKeyboardBuilder()
    for text, callback_data in zip(meanings_button['text'], meanings_button['callback_data']):
        builder.button(text = text, callback_data = callback_data)

    builder.adjust(3)

    return builder.as_markup()


@router.callback_query(F.data.startswith('meaning_'))
async def meaning_cb(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    num = await get_data(call.message.message_id)
    theme = call.data.split('_')[2]
    choice = call.data.split('_')[1]
    table = f"meaning_{choice}"
    keyboard = await generate_meaning_keyboard(choice, call.data)

    meaning_text = await execute_select(f"SELECT {theme} FROM {table} WHERE number = $1;", (num,))

    if len(meaning_text) > 4096:
        meaning_text = meaning_text[:4000]

    text = meaning_text + f"\n\n<a href = '{MEANINGS_BUTTONS[choice]['source']}'>Источник</a>"

    await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                text = text, reply_markup = keyboard)


@router.callback_query(F.data == 'menu_return')
async def menu_return(call: types.CallbackQuery):
    await call.answer()
    # await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.message.answer(text = f'Вот тебе меню!', reply_markup = kb.menu_private_keyboard)
