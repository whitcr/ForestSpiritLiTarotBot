from aiogram import types, Router, F, Bot
from constants import DECK_MAP
from database import execute_query
from filters.subscriptions import SubscriptionLevel
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

router = Router()


async def generate_decks_keyboard():
    builder = InlineKeyboardBuilder()

    for key, value in DECK_MAP.items():
        builder.button(text = value, callback_data = key)

    builder.adjust(3)
    return builder.as_markup()


@router.message(F.text.lower() == "колода")
async def choose_deck_menu(message: types.Message):
    keyboard = await generate_decks_keyboard()
    await message.reply("— Выберите колоду, на которой хотите гадать: ",
                        reply_markup = keyboard)


@router.callback_query(F.data.startswith("change_deck"))
async def choose_deck_menu_cb(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    keyboard = await generate_decks_keyboard()
    await bot.send_message(chat_id = call.message.chat.id, text = "— Выберите колоду, на которой хотите гадать: ",
                           reply_markup = keyboard, reply_to_message_id = call.message.reply_to_message.message_id)


async def set_user_cards_type(bot: Bot, call: types.CallbackQuery, cards_type, cards_name):
    user_id = call.from_user.id
    await execute_query(
        "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id",
        (call.from_user.id,))
    await execute_query("UPDATE users SET cards_type =$1 WHERE user_id = $2", (cards_type, user_id))
    await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                text = f"— {cards_name} приветствует вас!")


@router.callback_query(lambda call: call.data in DECK_MAP.keys())
async def handle_card_type(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        cards_name = DECK_MAP[call.data]
        await set_user_cards_type(bot, call, call.data, cards_name)
    else:
        pass
