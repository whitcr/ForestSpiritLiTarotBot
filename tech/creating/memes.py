import random

from PIL import Image, ImageDraw

from aiogram import types, Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from constants import FONT_L

from database import execute_select, execute_query
from filters.baseFilters import IsAdmin
from functions.cards.create import get_choice_spread, get_buffered_image

router = Router()


class Meme(StatesGroup):
    photo = State()
    card = State()
    place = State()


@router.callback_query(IsAdmin(), StateFilter(None), F.data == 'create_mem')
async def create_mem(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Отправьте изображение")
    await state.set_state(Meme.photo)


@router.message(content_types = ['photo'], state = Meme.photo)
async def get_meme_photo(message: types.Message, state: FSMContext, bot: Bot):
    meme = await bot.get_file(message.photo[-1].file_id)
    await meme.download(destination_file = './images/schedule/memes/meme.jpg')
    await message.answer("Какую карту разместить?")
    await state.set_state(Meme.card)


@router.message(Meme.card)
async def get_meme_card(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(Card_meme = message.text.lower())
    data = await state.get_data()
    card = str(data['Card_meme'])

    num = await execute_select("select number from meaning_raider where name = $1;", (card,))

    choice = await get_choice_spread(message.from_user.id)
    card_path = f"./images/cards/{choice}/{num}.jpg"

    card = Image.open(card_path).resize((1400, 2160))
    photo = Image.open('./images/schedule/memes/meme.jpg')

    max_x = card.width - photo.width
    max_y = card.height - photo.height
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)

    resize_ratio = min(card.width / photo.width, card.height / photo.height)
    new_size = (int(photo.width * resize_ratio), int(photo.height * resize_ratio))
    insert_image = photo.resize(new_size)

    card.paste(insert_image, (x, y))

    draw_text = ImageDraw.Draw(card)
    draw_text.text((240, 8), '@ForestSpiritLi', font = FONT_L, fill = 'black')

    msg = await bot.send_photo(message.chat.id, photo = await get_buffered_image(insert_image))
    file_id = msg.photo[-1].file_id
    await execute_query("insert into memes(memes) values('{}')".format(file_id))

    await state.clear()
