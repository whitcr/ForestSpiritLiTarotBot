from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from filters.baseFilters import IsAdmin

router = Router()

builder = InlineKeyboardBuilder()

buttons = [
    ("Мем", "create_mem"),
    ("Момент", "create_moment"),
    ("Текст на картинке", "create_text"),
    ("Карту с текстом", "create_photo_text"),
    ("2 карты", "create_2_cards"),
    ("3 карты", "create_3_cards"),
    ("Заливка", "create_zalivka"),
    ("Аффирмация", "create_affirmation"),
    ("Мантра", "create_mantra"),
    ("Медитация", "create_meditation"),
    ("Саблиминал", "create_sab"),
    ("2 карты с текстом", "create_2_card_text"),
    ("Текст для поста", "post_text"),
]

for text, data in buttons:
    builder.button(text = text, callback_data = data)

builder.adjust(3, 2)


@router.message(IsAdmin(), F.text.lower() == "создать")
async def create_menu(message: types.Message):
    await message.answer("Чего сотворить хотите?", reply_markup = builder.as_markup())
