from aiogram import executor, types
from bot import dp, db, bot, cursor
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFilter
from io import BytesIO
import asyncio
from random import randint
import numpy as np
import textwrap
from datetime import datetime
import pytz
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import IDFilter
from aiogram.types import ContentType, Message
import random
from aiogram.utils.markdown import hlink
import keyboard as kb
from constants import ADMIN_ID, CHANNEL_ID
from .getDailyPosts import get_post_template
from constants import P_FONT_L, P_FONT_XL, P_FONT_S
from functions import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread, get_random_num,\
    delete_message, get_colors_background


class Posting(StatesGroup):
    card_answer = State()


class get_post_image(StatesGroup):
    text = State()


class common_spread(StatesGroup):
    cards = State()


@dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.lower().startswith("запостить"))
async def get_posting(message: types.Message):
    await message.answer("Чего постим?", reply_markup = kb.posting_keyboard)


@dp.callback_query_handler(IDFilter(user_id = ADMIN_ID), lambda call: call.data == 'post_text')
async def get_post_text(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("Введи заголовок")

    await get_post_image.text.set()


@dp.message_handler(state = get_post_image.text)
async def post_text(message: types.Message, state: FSMContext):
    await state.update_data(text = message.text)
    data = await state.get_data()
    text = str(data['text']).upper()

    background_path = await get_path_background()

    color = Image.open('./images/tech/design_posts/backcolor.png').convert("RGBA")

    background = Image.open(background_path).convert("RGBA")
    background = background.resize((1920, 1080))

    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, background, alpha = .2)

    num = randint(1, 6)
    path_design = Image.open(f'./images/tech/design_posts/{num}.png').convert("RGBA")
    image.paste(path_design, (1, 1), path_design)

    draw = ImageDraw.Draw(image)
    para = textwrap.wrap(text, width = 10)

    draw.text((760, 980), 'ДЫХАНИЕ ЛЕСА', font = P_FONT_L, fill = 'white')
    length = len(para)
    if length == 1:
        current_h, pad = 370, 10
        FONT = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 300)
    elif length == 2:
        current_h, pad = 270, 10
        FONT = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 250)

    for line in para:
        w, h = text_size(line, FONT)
        draw.text(((1920 - w) / 2, current_h), line, font = FONT)
        current_h += h + pad

    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)

    await bot.send_photo(message.chat.id, photo = bio)
    db.commit()

    await state.finish()


@dp.message_handler((IDFilter(user_id = ADMIN_ID)), lambda message: message.text.lower().startswith("!общий"))
async def get_image_common_spread(message: types.Message):
    text = " ".join(message.text.split(" ")[1:]).split("-")[0]
    cards_names = message.text.split("-")[1:]

    text = " ".join(text)

    image = await get_post_template()

    cards = Image.open('./images/tech/design_posts/common_spread.png').convert("RGBA")

    image.paste(cards, (1, 1), cards)

    choice = await get_choice_spread(message.from_user.id)
    cards_path = []
    for card in cards_names:
        cursor.execute("SELECT number FROM meaning_raider where name = %s", (card,))
        num = cursor.fetchone()[0]
        card_path = await get_path_cards(choice, num)
        cards_path.append(card_path)

    draw = ImageDraw.Draw(image)
    para = textwrap.wrap(text.upper(), width = 50)

    length = len(para)
    if length == 1:
        current_h, pad = 160, 10
        FONT = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 100)
    elif length == 2:
        current_h, pad = 140, 10
        FONT = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 80)

    for line in para:
        w, h = text_size(line, FONT)
        draw.text(((1920 - w) / 2, current_h), line, font = FONT)
        current_h += h + pad

    draw.text((735, 15), 'ОБЩИЙ РАСКЛАД', font = P_FONT_L, fill = 'white')
    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)

    await bot.send_photo(message.chat.id, photo = bio)

    w, h = 370, 620;
    x, y = 85, 333

    card = Image.open(cards_path[0])
    card = card.resize((w, h))
    image.paste(card, (x, y))

    card = Image.open(cards_path[1])
    card = card.resize((w, h))
    image.paste(card, (2 * x + w, y))

    card = Image.open(cards_path[2])
    card = card.resize((w, h))
    image.paste(card, (3 * x + 2 * w, y))

    card = Image.open(cards_path[3])
    card = card.resize((w, h))
    image.paste(card, (4 * x + 3 * w + 5, y))

    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)

    await bot.send_photo(message.chat.id, photo = bio)


@dp.callback_query_handler((IDFilter(user_id = ADMIN_ID)), lambda call: call.data == 'meme_posting')
async def get_meme_posting(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await posting_memes()


async def posting_memes():
    try:
        group = types.MediaGroup()
        for i in range(4):
            cursor.execute("select number from memes ORDER BY number")
            min = cursor.fetchone()[0]
            cursor.execute("select memes from memes where number = {}".format(min))
            meme = cursor.fetchone()[0]
            group.attach_photo(photo = meme)
            cursor.execute("delete from memes where number = {}".format(min))
            db.commit()

        await bot.send_media_group(CHANNEL_ID, media = group)
    except:
        pass
