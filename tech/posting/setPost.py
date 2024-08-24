from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFilter
from random import randint
import textwrap
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import types, F, Router, Bot
import keyboard as kb
from constants import P_FONT_L
from filters.baseFilters import IsAdmin
from functions.cards.create import get_path_background, text_size, get_buffered_image

router = Router()


class Posting(StatesGroup):
    card_answer = State()


class GetPostImage(StatesGroup):
    text = State()


class CommonSpread(StatesGroup):
    cards = State()


@router.message(IsAdmin(), F.text.lower().startswith("запостить"))
async def get_posting(message: types.Message):
    await message.answer("Чего постим?", reply_markup = kb.posting_keyboard)


@router.callback_query(StateFilter(None), IsAdmin(), F.data == 'post_text')
async def get_post_text(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Введи заголовок")

    await state.set_state(GetPostImage.text)


@router.message(GetPostImage.text)
async def post_text(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(text = message.text)
    data = await state.get_data()
    text = str(data['text']).upper()

    background_path = await get_path_background()

    color = Image.open('./cards/tech/design_posts/backcolor.png').convert("RGBA")

    background = Image.open(background_path).convert("RGBA")
    background = background.resize((1920, 1080))

    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, background, alpha = .2)

    num = randint(1, 6)
    path_design = Image.open(f'./cards/tech/design_posts/{num}.png').convert("RGBA")
    image.paste(path_design, (1, 1), path_design)

    draw = ImageDraw.Draw(image)
    para = textwrap.wrap(text, width = 10)

    draw.text((760, 980), 'ДЫХАНИЕ ЛЕСА', font = P_FONT_L, fill = 'white')
    length = len(para)
    if length == 1:
        current_h, pad = 370, 10
        FONT = ImageFont.truetype("./cards/tech/fonts/1246-font.otf", 300)
    elif length == 2:
        current_h, pad = 270, 10
        FONT = ImageFont.truetype("./cards/tech/fonts/1246-font.otf", 250)

    for line in para:
        w, h = text_size(line, FONT)
        draw.text(((1920 - w) / 2, current_h), line, font = FONT)
        current_h += h + pad

    await bot.send_photo(message.chat.id, photo = await get_buffered_image(image))

    await state.clear()
