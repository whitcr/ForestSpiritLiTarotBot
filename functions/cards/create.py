from io import BytesIO

from PIL import ImageDraw
from aiogram.types import BufferedInputFile

from database import execute_select
import random
from random import randint
import itertools
import asyncio
import numpy as np
from PIL import Image
import asyncio
import time
import logging
from contextlib import contextmanager
from functions.statistics.cards import get_user_card_statistics, get_statistic_card


async def get_choice_spread(user_id):
    try:
        result = await execute_select("SELECT cards_type FROM users WHERE user_id = $1", (user_id,))

        return result if result else "raider"
    except Exception as e:
        return "raider"


logging.basicConfig(level = logging.INFO, format = '%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


@contextmanager
def timing(operation):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info(f"{operation}: {elapsed:.3f} seconds")


async def get_random_num(choice, count, user_id=None):
    with timing("get_random_num"):
        min_max_map = {
            "vikaoracul": (0, 47),
            "vikanimaloracul": (0, 47),
            "lenorman": (1, 35),
            "animalspirit": (0, 63),
            "tarot": (1, 77),
        }
        min_num, max_num = min_max_map.get(choice, (1, 77))

        if count == 1:
            num = random.randint(min_num, max_num)
            logger.info(f"Generated random number: {num}")

            if user_id:
                with timing("get_user_card_statistics and get_statistic_card"):
                    task1 = asyncio.create_task(get_user_card_statistics(user_id = user_id, num = num))
                    task2 = asyncio.create_task(get_statistic_card(num))
                    await asyncio.gather(task1, task2)
            return num
        else:
            nums = random.sample(range(min_num, max_num + 1), count) if min_num == 1 else list(
                itertools.islice(random.randint(0, max_num), count))
            logger.info(f"Generated {len(nums)} random numbers: {nums}")

            if user_id:
                with timing("all get_user_card_statistics and get_statistic_card calls"):
                    tasks = [
                        asyncio.create_task(get_user_card_statistics(user_id = user_id, num = num))
                        for num in nums
                    ]
                    tasks.extend([
                        asyncio.create_task(get_statistic_card(num))
                        for num in nums
                    ])
                    await asyncio.gather(*tasks)
            return nums


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
    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'PNG')
        bio.seek(0)
        image_to_send = BufferedInputFile(bio.getvalue(), "image.png")
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
