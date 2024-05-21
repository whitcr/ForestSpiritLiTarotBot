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
import random
import keyboard as kb
from constants import ADMIN_ID
from functions import get_path_cards, get_choice_spread
from constants import FONT_L

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

create_mem_button = InlineKeyboardButton(text = "Мем", callback_data = "create_mem")
create_moment_button = InlineKeyboardButton(text = "Момент", callback_data = "create_moment")
create_text_button = InlineKeyboardButton(text = "Текст на картинке", callback_data = "create_text")
create_photo_text_button = InlineKeyboardButton(text = "Карту с текстом", callback_data = "create_photo_text")
create_2_cards__button = InlineKeyboardButton(text = "2 карты", callback_data = "create_2_cards")
create_3_cards__button = InlineKeyboardButton(text = "3 карты", callback_data = "create_3_cards")
create_zalivka__button = InlineKeyboardButton(text = "Заливка", callback_data = "create_zalivka")
create_affirmation__button = InlineKeyboardButton(text = "Аффирмация", callback_data = "create_affirmation")
create_mantra__button = InlineKeyboardButton(text = "Мантра", callback_data = "create_mantra")
create_meditation__button = InlineKeyboardButton(text = "Медитация", callback_data = "create_meditation")
create_sab__button = InlineKeyboardButton(text = "Саблиминал", callback_data = "create_sab")
create_2_card_text__button = InlineKeyboardButton(text = "2 карты с текстом", callback_data = "create_2_card_text")
post_text_button = InlineKeyboardButton(text = "Текст для поста", callback_data = "post_text")
create_keyboard = InlineKeyboardMarkup(resize_keyboard = True).add(create_mem_button, create_moment_button,
                                                                   create_text_button, create_photo_text_button,
                                                                   create_2_cards__button, create_2_card_text__button,
                                                                   create_3_cards__button,
                                                                   create_zalivka__button, create_affirmation__button,
                                                                   create_mantra__button, create_meditation__button,
                                                                   create_sab__button, post_text_button)

messages = []


class Meme(StatesGroup):
    photo = State()
    card = State()
    place = State()


@dp.message_handler(IDFilter(user_id = ADMIN_ID), lambda message: message.text.lower() == "создать")
async def create_menu(message: types.Message):
    msg = await message.answer("Чего сотворить хотите?", reply_markup = create_keyboard)


@dp.callback_query_handler(IDFilter(user_id = ADMIN_ID), lambda call: call.data == 'create_mem')
async def create_mem(call: types.CallbackQuery, state="*"):
    await call.answer()
    msg = await call.message.answer("Отправьте изображение")
    await Meme.photo.set()


@dp.message_handler(content_types = ['photo'], state = Meme.photo)
async def get_meme_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    meme = await bot.get_file(message.photo[-1].file_id)
    await meme.download(destination_file = './images/schedule/memes/meme.jpg')
    msg = await message.answer("Какую карту разместить?")
    await Meme.card.set()


@dp.message_handler(state = Meme.card)
async def get_meme_card(message: types.Message, state: FSMContext):
    await state.update_data(Card_meme = message.text.lower())
    data = await state.get_data()
    card = str(data['Card_meme'])

    cursor.execute("select number from meaning_raider where name = %s;", (card,))
    num = cursor.fetchone()[0]

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

    bio = BytesIO()
    bio.name = 'image.jpeg'
    card.save(bio, 'JPEG')
    bio.seek(0)

    msg = await bot.send_photo(message.chat.id, photo = bio)
    file_id = msg.photo[-1].file_id
    cursor.execute("insert into memes(memes) values('{}')".format(file_id))
    db.commit()
    await state.finish()

# @dp.message_handler(IDFilter(user_id=ADMIN_ID),lambda message: message.text.lower().startswith("мем"))
# async def get_meme(message: types.Message):
#     if message.reply_to_message:
#         card_name = message.text.split(" ")[1]
#         text = message.reply_to_message.text
#         username = message.reply_to_message.from_user.first_name
#         file = await message.reply_to_message.from_user.get_profile_photos()
#         photo = file.photos[0][1].file_id
#
#         await create_meme(message, card_name, text)
#
#         print(card_name, text, username, photo)
#     else:
#         await Meme.messages.set()
#
#
# @dp.message_handler(state = Meme.messages)
# async def process_messages(message: types.Message, state: FSMContext):
#     messages.append(message.text)
#
#
# @dp.message_handler(state=Meme.messages, commands=['создать'], commands_prefix='!',)
# async def finish_command(message: types.Message, state: FSMContext):
#     await state.finish()
#
#     await bot.send_message(message.chat.id, "Ввод завершен. Спасибо!")
#
#
# async def create_meme(message, card_name, text):
#     cursor.execute("select number from description where name = %s;", (card_name, ))
#     num = cursor.fetchone()[0]
#
#     choice = await get_choice_spread(message.from_user.id)
#     card_path = await get_path_cards(choice, num)
#
#     card = Image.open(card_path).resize((700, 1080))
#     card.save("./images/schedule/memes/card.png")
#     card = Image.open('./images/schedule/memes/card.png').convert("RGBA")
#     template = Image.open('./images/schedule/memes/memes_small.png').convert("RGBA").resize((500, 100))
#
#     # card.paste(template, (130, 50))
#
#     card = Image.blend(card, template, alpha = .3)
#
#     draw = ImageDraw.Draw(card)
#     para = textwrap.wrap("— " + text, width = 30)
#     current_h, pad = 250, 10
#     for line in para:
#         w, h = text_size(line, FONT_L)
#         draw.text(((1920 - w) / 2, current_h), line, font = FONT_L)
#         current_h += h + pad
#
#     bio = BytesIO()
#     bio.name = 'image.png'
#     with bio:
#         card.save(bio, 'PNG')
#         bio.seek(0)
#         await bot.send_photo(message.chat.id, photo=bio)
