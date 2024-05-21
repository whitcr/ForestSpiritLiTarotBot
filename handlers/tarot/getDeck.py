from aiogram import types, Router, F
from constants import DECK_MAP
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from main import bot

router = Router()


async def generate_decks_keyboard():
    buttons = []
    for key, value in DECK_MAP.items():
        button = InlineKeyboardButton(text = value, callback_data = key)
        buttons.append(button)

    choose_cards_keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 3).add(*buttons)
    return choose_cards_keyboard


@router.message(F.text.lower() == "колода")
async def choose_deck_menu(message: types.Message):
    keyboard = await generate_decks_keyboard()
    await message.reply("— Выберите колоду, на которой хотите гадать: ",
                        reply_markup = keyboard)


async def set_user_cards_type(call: types.CallbackQuery, cards_type, cards_name):
    user_id = call.from_user.id
    execute_query(
        "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id",
        (call.from_user.id,))
    execute_query("UPDATE users SET cards_type = %s WHERE user_id = %s", (cards_type, user_id))
    await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                text = f"— {cards_name} приветствует вас!")


@router.callback_query(lambda call: call.data in DECK_MAP.keys())
async def handle_card_type(call: types.CallbackQuery):
    await call.answer()
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        cards_name = DECK_MAP[call.data]
        await set_user_cards_type(call, call.data, cards_name)
    else:
        pass
