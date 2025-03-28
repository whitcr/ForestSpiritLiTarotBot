import requests
from aiogram import types, Router, Bot

from filters.baseFilters import IsReply
from handlers.tarot.spreads.meaningSpreads.getMeaningSpread import create_gpt_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from functions.cards.create import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread,\
    get_random_num, get_colors_background, text_size, get_buffered_image
from PIL import Image, ImageDraw
from PIL import ImageFilter
import numpy as np
import pendulum
from constants import (FONT_L)
import textwrap
from io import BytesIO
from aiogram.types import InputMediaPhoto
import re
from handlers.tarot.spreads.spreadsConfig import SPREADS, get_name_by_cb_key
from aiogram.filters.callback_data import CallbackData
from typing import Optional

from middlewares.statsUser import use_user_statistics

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
    for text, font in SPREADS[spread_name]['image']:
        para = textwrap.wrap(text, width = 30)
        for line in para:
            w, h = text_size(line, font)
            draw_text.text(((pad - w) / 2, current_h), line, font = font)
        pad += 1300
    return image


async def create_keyboard_dops(nums, position, spread_name=None):
    text = ["Доп карта", "Доп карта", "Доп карта"]

    callback_data = [
        NumbersCallbackFactory(position = i + 1, card_1 = nums[0], pcard_1 = position[0],
                               card_2 = nums[1], pcard_2 = position[1], card_3 = nums[2],
                               pcard_3 = position[2], spread_name = spread_name if spread_name else None).pack()
        for i in range(3)
    ]

    empty_button = []
    for i, element in enumerate(position):
        if element > 3:
            empty_button.append(i)

    for index in empty_button:
        text[index] = ""
        callback_data[index] = "empty"

    buttons = [[InlineKeyboardButton(text = text[0], callback_data = callback_data[0]),
                InlineKeyboardButton(text = text[1], callback_data = callback_data[1]),
                InlineKeyboardButton(text = text[2], callback_data = callback_data[2])]]

    return buttons


async def generate_dop(choice, call):
    async def parse_callback_data(callback_data):
        parts = callback_data.replace('get_def_gpt_:', '').split(':')
        numbers = [int(part) for part in parts if part]
        return numbers

    numbers = await parse_callback_data(call.message.reply_markup.inline_keyboard[1][0].callback_data)

    random_number = await get_random_num(choice, 1, call.from_user.id)
    while random_number in numbers:
        random_number = await get_random_num(choice, 1, call.from_user.id)

    return random_number


@router.callback_query(IsReply(), NumbersCallbackFactory.filter())
async def process_callback_get_dop(call: types.CallbackQuery, bot: Bot,
                                   callback_data: NumbersCallbackFactory, api_token: str):
    await call.answer()
    user_id = call.from_user.id

    spread_name = getattr(callback_data, 'spread_name', None)

    nums = [callback_data.card_1, callback_data.card_2, callback_data.card_3]
    dop_positions = [callback_data.pcard_1, callback_data.pcard_2, callback_data.pcard_3]
    card_position = callback_data.position
    prev_callback_data_gpt = call.message.reply_markup.inline_keyboard[-1][0].callback_data
    image = call.message.photo[-1].file_id

    image, positions, dop_num, card_position = await get_image_with_dops(api_token,
                                                                         user_id, nums, card_position, dop_positions,
                                                                         image, call, spread_name
                                                                         )

    await send_image_dops(bot, call, image, nums, positions, prev_callback_data_gpt, dop_num, card_position,
                          spread_name = spread_name)


async def get_image_with_dops(api_token, user_id, nums, card_position, dop_positions, image, message, spread_name=None):
    choice = await get_choice_spread(user_id)
    dop_num = await generate_dop(choice, message)

    if any(element > 1 for element in dop_positions):
        url = f'https://api.telegram.org/bot{api_token}/getFile'

        response = requests.get(url, params = {'file_id': image})
        data = response.json()
        file_path = data['result']['file_path']

        file_url = f'https://api.telegram.org/file/bot{api_token}/{file_path}'

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

    if dop_positions[0] == 2 and card_position == 1:
        dop_positions[0] += 1
        image.paste(dop, (220, 730))
    elif dop_positions[0] == 3 and card_position == 1:
        dop_positions[0] += 1
        image.paste(dop, (410, 730))
    elif dop_positions[0] == 1 and card_position == 1:
        dop_positions[0] += 1
        image.paste(dop, (30, 730))
    elif dop_positions[1] == 2 and card_position == 2:
        dop_positions[1] += 1
        image.paste(dop, (640 + 220, 730))
    elif dop_positions[1] == 3 and card_position == 2:
        dop_positions[1] += 1
        image.paste(dop, (640 + 410, 730))
    elif dop_positions[1] == 1 and card_position == 2:
        dop_positions[1] += 1
        image.paste(dop, (640 + 30, 730))
    elif dop_positions[2] == 2 and card_position == 3:
        dop_positions[2] += 1
        image.paste(dop, (640 * 2 + 230, 730))
    elif dop_positions[2] == 3 and card_position == 3:
        dop_positions[2] += 1
        image.paste(dop, (640 * 2 + 420, 730))
    elif dop_positions[2] == 1 and card_position == 3:
        dop_positions[2] += 1
        image.paste(dop, (640 * 2 + 40, 730))

    return image, dop_positions, dop_num, card_position


async def send_image_dops(bot, message, image, nums, position, prev_callback_data_gpt, dop_num, card_position,
                          spread_name):
    buttons = await create_keyboard_dops(nums, position, spread_name = spread_name)
    buttons = await create_gpt_keyboard(message.message.from_user.id, buttons, nums, prev_callback_data_gpt,
                                        card_position, dop_num,
                                        spread_name = spread_name)
    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    await bot.edit_message_media(chat_id = message.message.chat.id,
                                 message_id = message.message.message_id,
                                 media = InputMediaPhoto(media = await get_buffered_image(image)),
                                 reply_markup = keyboard)
