from aiogram import types, Router
from main import dp, bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


async def generate_keyboard(callback_data):
    buttons = [
        InlineKeyboardButton(text = "Любовь", callback_data = "love_questions"),
        InlineKeyboardButton(text = "О себе", callback_data = "myself_questions"),
        InlineKeyboardButton(text = "Общество", callback_data = "social_questions"),
        InlineKeyboardButton(text = "Финансы", callback_data = "finance_questions")
    ]

    buttons = [b for b in buttons if b.callback_data != callback_data]

    keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 2)
    keyboard.add(*buttons)

    return keyboard


@router.message(lambda message: message.text.lower() == "вопросы")
async def get_menu_questions(message: types.Message):
    keyboard = await generate_keyboard("General")
    await message.reply("На какую тематику вы хотите получить список вопросов?", reply_markup = keyboard)


@router.callback_query(lambda call: call.data.endswith('_questions'))
async def get_questions(call: types.CallbackQuery):
    await call.answer()
    theme = call.data.split('_')[0]
    keyboard = await generate_keyboard(f"{theme}" + "_questions")
    with open(f"./handlers/tarot/questions/{theme}_questions.txt", "r") as file:
        questions = file.read()

    await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                text = questions, reply_markup = keyboard)
