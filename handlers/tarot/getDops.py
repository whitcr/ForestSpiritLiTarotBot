import requests
from aiogram import types, Router, F

from database import execute_select
from main import bot
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from functions.createImage import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread,\
    get_random_num, get_colors_background, text_size, get_buffered_image
from PIL import Image, ImageDraw
from PIL import ImageFilter
import numpy as np
import pendulum
from constants import (FONT_L)
from main import API_TOKEN
import textwrap
from io import BytesIO
from aiogram.types import InputMediaPhoto
import re
import time
from handlers.tarot.spreads.spreadsConfig import SPREADS
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from typing import Optional

router = Router()


class NumbersCallbackFactory(CallbackData, prefix = "get_dop_"):
    position: int
    card_1: int
    pcard_1: int
    card_2: int
    pcard_2: int
    card_3: int
    pcard_3: int
    spread_name: Optional[str]


async def draw_spread(image, spread_name):
    draw_text = ImageDraw.Draw(image)
    current_h, pad = 80, 600
    count = 0
    spread_name = spread_name
    for text, font in SPREADS[spread_name]['image']:
        count += 1
        para = textwrap.wrap(text, width = 30)
        for line in para:
            w, h = text_size(line, font)
            draw_text.text(((pad - w) / 2, current_h), line, font = font)
        pad += 1300
    return image


async def create_keyboard_dops(message, nums, position, spread_name=None):
    text = ["Доп карта", "Доп карта", "Доп карта"]

    callback_data = [
        NumbersCallbackFactory(position = i + 1, card_1 = nums[0], pcard_1 = position[0],
                               card_2 = nums[1], pcard_2 = position[1], card_3 = nums[2],
                               pcard_3 = position[2], spread_name = spread_name if spread_name else None).pack()
        for i in range(3)
    ]

    empty_button = [i for i, element in enumerate(position) if element > 3]

    for index in empty_button:
        text[index] = ""
        callback_data[index] = "empty"

    buttons = [[InlineKeyboardButton(text = text[0], callback_data = callback_data[0]),
                InlineKeyboardButton(text = text[1], callback_data = callback_data[1]),
                InlineKeyboardButton(text = text[2], callback_data = callback_data[2])]]

    return buttons


cooldowns = {}
dop_nums = {}


async def clear_cooldown(user_id, cooldown_duration):
    await asyncio.sleep(cooldown_duration)
    cooldowns.pop(user_id, None)


async def clear_dop_nums(message_id):
    dop_nums.pop(message_id, None)


async def add_dop_to_ignore(message_id, number):
    if message_id not in dop_nums:
        dop_nums[message_id] = []
    dop_nums[message_id].append(number)


async def generate_dop(message_id, choice):
    while True:
        random_number = await get_random_num(choice, 1)
        if message_id not in dop_nums or random_number not in dop_nums[message_id]:
            return random_number


@router.callback_query(NumbersCallbackFactory.filter())
async def process_callback_get_dop(call: types.CallbackQuery,
                                   callback_data: NumbersCallbackFactory):
    await call.answer()
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        user_id = call.from_user.id
        if user_id in cooldowns and time.time() - cooldowns[user_id] < 2:
            pass
        else:
            cooldowns[user_id] = time.time()
            asyncio.create_task(clear_cooldown(user_id, 2))
            try:
                spread_name = callback_data.spread_name

            except:
                spread_name = None

            nums = [callback_data.card_1, callback_data.card_2, callback_data.card_3]
            dop_positions = [callback_data.pcard_1, callback_data.pcard_2, callback_data.pcard_3]
            card_position = callback_data.position
            prev_callback_data_gpt = call.message.reply_markup.inline_keyboard[-1][0].callback_data
            image = call.message.photo[-1].file_id

            if spread_name is not None:
                image, positions, dop_num, card_position = await get_image_with_dops(user_id, nums, card_position,
                                                                                     dop_positions,
                                                                                     image, call,
                                                                                     spread_name)
            else:
                image, positions, dop_num, card_position = await get_image_with_dops(user_id, nums, card_position,
                                                                                     dop_positions,
                                                                                     image, call)

            await send_image_dops(call, image, nums, positions, prev_callback_data_gpt, dop_num, card_position)


async def get_image_with_dops(user_id, nums, card_position, dop_positions, image, message, spread_name=None):
    choice = await get_choice_spread(user_id)
    dop_num = await generate_dop(message.message.message_id, choice)

    if any(element > 1 for element in dop_positions):
        url = f'https://api.telegram.org/bot{API_TOKEN}/getFile'

        response = requests.get(url, params = {'file_id': image})
        data = response.json()
        file_path = data['result']['file_path']

        file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}'

        response = requests.get(file_url)
        image_data = response.content

        image = Image.open(BytesIO(image_data))

        dop_path = await get_path_cards(choice, dop_num)
        dop = Image.open(dop_path).resize((180, 300))
    else:
        col1, col2 = await get_colors_background(choice)

        if choice == 'deviantmoon' or choice == 'manara' or choice == 'aftertarot':
            x = 140
        elif choice == "vikaoracul" or choice == "vikanimaloracul":
            x = 80
        else:
            x = 150
        y = 140

        cards = np.random.randint(col1, col2, size = 6)
        array = get_gradient_3d(1920, 1080, (cards[0], cards[1], cards[2]), (cards[3], cards[4], cards[5]),
                                (True, False, True))
        color = Image.fromarray(np.uint8(array))

        for num in nums:
            await add_dop_to_ignore(message.message.message_id, int(num))

        dop_path = await get_path_cards(choice, dop_num)
        card_paths = [await get_path_cards(choice, nums[i]) for i in range(3)]

        images = []
        for i, path in enumerate(card_paths):
            card_image = Image.open(path).resize((320, 560))
            w, h = card_image.size
            images.append(card_image)

        background_path = await get_path_background()
        background = Image.open(background_path)
        background = background.resize((1920, 1080))
        background = background.filter(ImageFilter.GaussianBlur(radius = 3))
        image = Image.blend(color, background, alpha = .4)

        image.paste(images[2], ((3 * x + 2 * w + 340), y))
        image.paste(images[1], ((2 * x + w + 170), y))
        image.paste(images[0], (x, y))

        dop = Image.open(dop_path).resize((180, 300))

        date = pendulum.today('Europe/Kiev').format('DD.MM')
        draw_text = ImageDraw.Draw(image)
        draw_text.text((740, 1030), 'from @ForestSpiritLi', fill = 'white', font = FONT_L)
        draw_text.text((895, 10), date, fill = 'white', font = FONT_L)

        if spread_name is not None:
            await draw_spread(image, spread_name)
        else:
            text = message.message.reply_to_message.text.split(" ")[1:]
            text = ' '.join(text)
            draw_text = ImageDraw.Draw(image)
            if len(text) == 0:
                draw_text.text((870, 80), 'Триплет', fill = 'white', font = FONT_L)
            else:
                if re.search(r".+-.+-.+", text):
                    test = message.message.reply_to_message.text.split("-")
                    test[0] = test[0].replace('триплет', '')
                    count = 0
                    current_h, pad = 80, 630
                    for text in test:
                        count += 1
                        para = textwrap.wrap(text, width = 30)
                        for line in para:
                            w, h = text_size(line, FONT_L)
                            draw_text.text(((pad - w) / 2, current_h), line, font = FONT_L)
                        pad += 1260
                else:
                    current_h, pad = 80, 1910
                    para = textwrap.wrap(str(text), width = 100)
                    for line in para:
                        w, h = text_size(line, FONT_L)
                        draw_text.text(((pad - w) / 2, current_h), line, font = FONT_L)
    await add_dop_to_ignore(message.message.message_id, dop_num)

    if dop_positions[0] == 1 and card_position == 1:
        dop_positions[0] += 1
        image.paste(dop, (220, 730))
    elif dop_positions[0] == 2 and card_position == 1:
        dop_positions[0] += 1
        image.paste(dop, (410, 730))
    elif dop_positions[0] == 3 and card_position == 1:
        dop_positions[0] += 1
        image.paste(dop, (30, 730))
    elif dop_positions[1] == 1 and card_position == 2:
        dop_positions[1] += 1
        image.paste(dop, (640 + 220, 730))
    elif dop_positions[1] == 2 and card_position == 2:
        dop_positions[1] += 1
        image.paste(dop, (640 + 410, 730))
    elif dop_positions[1] == 3 and card_position == 2:
        dop_positions[1] += 1
        image.paste(dop, (640 + 30, 730))
    elif dop_positions[2] == 1 and card_position == 3:
        dop_positions[2] += 1
        image.paste(dop, (640 * 2 + 230, 730))
    elif dop_positions[2] == 2 and card_position == 3:
        dop_positions[2] += 1
        image.paste(dop, (640 * 2 + 420, 730))
    elif dop_positions[2] == 3 and card_position == 3:
        dop_positions[2] += 1
        image.paste(dop, (640 * 2 + 40, 730))

    return image, dop_positions, dop_num, card_position


async def send_image_dops(message, image, nums, position, prev_callback_data_gpt, dop_num, card_position):
    media = InputMediaPhoto(media = await get_buffered_image(image))

    buttons = await create_keyboard_dops(message, nums, position, spread_name = None)

    buttons = await create_gpt_keyboard(buttons, nums, prev_callback_data_gpt, card_position, dop_num)

    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    await bot.edit_message_media(chat_id = message.message.chat.id,
                                 message_id = message.message.message_id,
                                 media = media,
                                 reply_markup = keyboard)


@router.callback_query(F.data.startswith('empty'))
async def process_callback_empty_button(call: types.CallbackQuery):
    await call.answer()


class GptCallback(CallbackData, prefix = "get_gpt_"):
    card_1: int
    d1card_1: Optional[int]
    d2card_1: Optional[int]
    d3card_1: Optional[int]

    card_2: int
    d1card_2: Optional[int]
    d2card_2: Optional[int]
    d3card_2: Optional[int]

    card_3: int
    d1card_3: Optional[int]
    d2card_3: Optional[int]
    d3card_3: Optional[int]

    spread_name: Optional[str]


async def create_gpt_keyboard(buttons, nums, prev_callback_data=None, card_position=None, dop_num=None):
    if prev_callback_data is None or dop_num is None:
        callback_data = GptCallback(card_1 = nums[0], d1card_1 = None,
                                    d2card_1 = None,
                                    d3card_1 = None,
                                    card_2 = nums[1], d1card_2 = None,
                                    d2card_2 = None,
                                    d3card_2 = None,
                                    card_3 = nums[2], d1card_3 = None,
                                    d2card_3 = None,
                                    d3card_3 = None,
                                    spread_name = None).pack()
    else:
        callback = GptCallback.unpack(prev_callback_data)

        d1card_1, d2card_1, d3card_1, d1card_2, d2card_2, d3card_2, d1card_3, d2card_3, d3card_3 = (None, None, None,
                                                                                                    None, None, None,
                                                                                                    None, None, None)
        if card_position == 1:
            if callback.d1card_1 is not None:
                d1card_1 = callback.d1card_1
                if callback.d2card_1 is not None:
                    d2card_1 = callback.d2card_1
                    if callback.d3card_1 is not None:
                        d3card_1 = callback.d3card_1
                    else:
                        d3card_1 = dop_num
                else:
                    d2card_1 = dop_num
            else:
                d1card_1 = dop_num

        elif card_position == 2:
            if callback.d1card_2 is not None:
                d1card_2 = callback.d1card_2
                if callback.d2card_2 is not None:
                    d2card_2 = callback.d2card_2
                    if callback.d3card_2 is not None:
                        d3card_2 = callback.d3card_2
                    else:
                        d3card_2 = dop_num
                else:
                    d2card_2 = dop_num
            else:
                d1card_2 = dop_num

        elif card_position == 3:
            if callback.d1card_3 is not None:
                d1card_3 = callback.d1card_3
                if callback.d2card_3 is not None:
                    d2card_3 = callback.d2card_3
                    if callback.d3card_3 is not None:
                        d3card_3 = callback.d3card_3
                    else:
                        d3card_3 = dop_num
                else:
                    d2card_3 = dop_num
            else:
                d1card_3 = dop_num

        if callback.d1card_1 is not None:
            d1card_1 = callback.d1card_1
            if callback.d2card_1 is not None:
                d2card_1 = callback.d2card_1
                if callback.d3card_1 is not None:
                    d3card_1 = callback.d3card_1
        if callback.d1card_2 is not None:
            d1card_2 = callback.d1card_2
            if callback.d2card_2 is not None:
                d2card_2 = callback.d2card_2
                if callback.d3card_2 is not None:
                    d3card_2 = callback.d3card_2
        if callback.d1card_3 is not None:
            d1card_3 = callback.d1card_3
            if callback.d2card_3 is not None:
                d2card_3 = callback.d2card_3
                if callback.d3card_3 is not None:
                    d3card_3 = callback.d3card_3

        callback_data = GptCallback(card_1 = nums[0], d1card_1 = d1card_1 if d1card_1 else None,
                                    d2card_1 = d2card_1 if d2card_1 else None,
                                    d3card_1 = d3card_1 if d3card_1 else None,
                                    card_2 = nums[1], d1card_2 = d1card_2 if d1card_2 else None,
                                    d2card_2 = d2card_2 if d2card_2 else None,
                                    d3card_2 = d3card_2 if d3card_2 else None,
                                    card_3 = nums[2], d1card_3 = d1card_3 if d1card_3 else None,
                                    d2card_3 = d2card_3 if d2card_3 else None,
                                    d3card_3 = d3card_3 if d3card_3 else None,
                                    spread_name = None).pack()

    buttons.append([InlineKeyboardButton(text = 'Трактовка', callback_data = callback_data)])

    return buttons


@router.callback_query(GptCallback.filter())
async def get_gpt_response_cards_meaning(call: types.CallbackQuery,
                                         callback_data: GptCallback):
    await call.answer()
    data_dict = callback_data.model_dump()

    def format_callback_data(data):
        lines = []

        question = call.message.reply_to_message.text.replace("триплет", "")
        if question.strip():
            lines.append(f"Вопрос: {question.strip()}")

        spread_name = data.get('spread_name')
        if spread_name:
            lines.append(f"Расклад: {spread_name}")

        for i in range(1, 4):
            card = data.get(f'card_{i}')
            if card is not None:
                card_name = execute_select("SELECT name FROM cards WHERE number = %s", (card,))
                line = f"Карта {i}: {card_name}."
                additional_cards = []
                for j in range(1, 4):
                    d = data.get(f'd{str(j)}card_{i}')
                    if d is not None:
                        card_name_d = execute_select("SELECT name FROM cards WHERE number = %s", (d,))
                        additional_cards.append(card_name_d)
                if additional_cards:
                    line += f" Дополнительные карты: {', '.join(additional_cards)}"
                lines.append(line)
        return "\n".join(lines)

    formatted_data = format_callback_data(data_dict)

    print(formatted_data)
