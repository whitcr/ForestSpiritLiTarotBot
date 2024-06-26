from io import BytesIO

from PIL import ImageDraw
from aiogram.types import BufferedInputFile

from database import execute_select
import random
from random import randint
import itertools
import numpy as np
from PIL import Image

import asyncio


async def get_choice_spread(user_id):
    try:
        result = execute_select("SELECT cards_type FROM users WHERE user_id = %s", user_id)

        return result if result else "raider"
    except Exception as e:
        return "raider"


def get_random_num_sync(choice, count):
    min_num = 0 if choice in {"vikaoracul", "vikanimaloracul", "animalspirit"} else 1
    max_num = {
        "vikaoracul": 47,
        "vikanimaloracul": 47,
        "lenorman": 35,
        "animalspirit": 63,
        "tarot": 77,
    }.get(choice, 77)

    if count == 1:
        return random.randint(min_num, max_num)
    else:
        return random.sample(range(min_num, max_num + 1), count) if min_num == 1 else list(
            itertools.islice(random.randint(0, max_num), count))


async def get_random_num(choice, count):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_random_num_sync, choice, count)


async def get_path_background():
    num = randint(1, 83)
    path = f"./images/tech/background/{num}.jpg"
    return path


async def get_path_cards(choice, num):
    return f"./images/cards/{choice}/{num}.jpg"


def get_path_cards_sync(choice, num):
    return f"./images/cards/{choice}/{num}.jpg"


async def get_colors_background(choice):
    if choice == 'deviantmoon' or choice == 'manara' or choice == 'aftertarot':
        col1, col2 = 0, 80
    elif choice == "vikaoracul" or choice == "vikanimaloracul":
        col1, col2 = 0, 50
    else:
        col1, col2 = 0, 150

    return col1, col2


def text_size(text, font):
    im = Image.new(mode = "P", size = (0, 0))
    draw = ImageDraw.Draw(im)
    _, _, width, height = draw.textbbox((0, 0), text = text, font = font)
    return width, height


async def get_buffered_image(image):
    with BytesIO() as buffer:
        image.save(buffer, 'PNG')
        buffer.seek(0)
        image_to_send = BufferedInputFile(buffer.getvalue(), "image.png")
    return image_to_send


def get_gradient_2d(start, stop, width, height, is_horizontal):
    if is_horizontal:
        return np.tile(np.linspace(start, stop, width), (height, 1))
    else:
        return np.tile(np.linspace(start, stop, height), (width, 1)).T


def get_gradient_3d(width, height, start_list, stop_list, is_horizontal_list):
    result = np.zeros((height, width, len(start_list)), dtype = float)

    for i, (start, stop, is_horizontal) in enumerate(zip(start_list, stop_list, is_horizontal_list)):
        result[:, :, i] = get_gradient_2d(start, stop, width, height, is_horizontal)

    return result
