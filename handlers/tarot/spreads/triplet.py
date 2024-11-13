from functools import lru_cache
from random import randint
import asyncio
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List
import numpy as np
from aiogram.types import InlineKeyboardMarkup, BufferedInputFile
from functions.cards.create import get_choice_spread, get_colors_background, get_gradient_3d,\
    get_path_background, get_path_cards, get_random_num, text_size, get_buffered_image
from functions.messages.messages import get_reply_message
from PIL import Image
from PIL import ImageFilter
import pendulum
from constants import FONT_S
import re
import textwrap
from PIL import ImageDraw
from aiogram import types, Router, F, Bot
from constants import FONT_L
from functions.cards.create import text_size
from functions.messages.messages import typing_animation_decorator
from .meaningSpreads.getMeaningSpread import create_gpt_keyboard
from ..dops.dopCard import create_keyboard_dops

# Создаем thread pool для операций с изображениями
image_thread_pool = ThreadPoolExecutor(max_workers = 4)
router = Router()


# Кэширование путей и загрузки изображений
@lru_cache(maxsize = 100)
def load_card_image(path: str) -> Image.Image:
    return Image.open(path)


@lru_cache(maxsize = 1)
def load_background(path) -> Image.Image:
    background = Image.open(path)
    background = background.resize((1920, 1080))
    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    return background


# Кэширование градиентов
@lru_cache(maxsize = 50)
def calculate_gradient(width: int, height: int, start_rgb: Tuple[int, int, int],
                       end_rgb: Tuple[int, int, int], is_horizontal: Tuple[bool, bool, bool]) -> np.ndarray:
    return get_gradient_3d(width, height, start_rgb, end_rgb, is_horizontal)


class TripletCardHandler:
    def __init__(self):
        self.card_cache = {}
        self.background = None

    async def initialize(self):
        """Асинхронная инициализация часто используемых ресурсов"""
        if not self.background:
            image = await get_path_background()
            background = Image.open(image)
            background = background.resize((1920, 1080))
            self.background = background.filter(ImageFilter.GaussianBlur(radius = 3))

    async def process_image(self, image: Image.Image, text: str, username: str,
                            date: str) -> Image.Image:
        """Асинхронная обработка изображения"""

        def _draw_text():
            draw = ImageDraw.Draw(image)

            # Отрисовка базовой информации
            draw.text((759, 990), 'from @ForestSpiritLi', fill = 'white', font = FONT_L)
            draw.text((895, 10), date, fill = 'white', font = FONT_L)

            # Обработка основного текста
            if not text:
                draw.text((870, 80), 'Триплет', fill = 'white', font = FONT_L)
            elif re.search(r".+-.+-.+", text):
                parts = text.split("-")
                current_h, pad = 80, 695
                for part in parts:
                    lines = textwrap.wrap(part.strip(), width = 30)
                    for line in lines:
                        w, h = text_size(line, FONT_L)
                        draw.text(((pad - w) / 2, current_h), line, font = FONT_L)
                    pad += 1210
            else:
                current_h, pad = 80, 1910
                lines = textwrap.wrap(text, width = 100)
                for line in lines:
                    w, h = text_size(line, FONT_L)
                    draw.text(((pad - w) / 2, current_h), line, font = FONT_L)

            # Отрисовка имени пользователя
            username_lines = textwrap.wrap(f"for {username}", width = 30)
            current_h, pad = 1040, 10
            for line in username_lines:
                w, h = text_size(line, FONT_S)
                draw.text(((1910 - w) / 2, current_h), line, font = FONT_S)
                current_h += h + pad

        await asyncio.get_event_loop().run_in_executor(image_thread_pool, _draw_text)
        return image

    async def get_image_three_cards(self, user_id: int) -> Tuple[Image.Image, List[int]]:
        """Асинхронное создание изображения с тремя картами"""
        choice = await get_choice_spread(user_id)

        # Определение отступов в зависимости от колоды
        x = {
            'deviantmoon': 140,
            'manara': 140,
            'aftertarot': 140,
            'vikaoracul': 80,
            'vikanimaloracul': 80
        }.get(choice, 105)
        y = 140

        # Параллельное получение случайных чисел и путей карт
        nums = await get_random_num(choice, 3, user_id)
        card_paths = await asyncio.gather(*[
            get_path_cards(choice, num) for num in nums
        ])

        # Загрузка изображений карт в отдельных потоках
        cards = await asyncio.gather(*[
            asyncio.get_event_loop().run_in_executor(
                image_thread_pool, lambda p=path: load_card_image(p)
            ) for path in card_paths
        ])

        # Создание градиента и фона
        col1, col2 = await get_colors_background(choice)
        cards_rgb = np.random.randint(col1, col2, size = 6)
        gradient = await asyncio.get_event_loop().run_in_executor(
            image_thread_pool,
            lambda: calculate_gradient(1920, 1080,
                                       tuple(cards_rgb[:3]),
                                       tuple(cards_rgb[3:]),
                                       (True, False, True))
        )

        # Создание финального изображения
        color = Image.fromarray(np.uint8(gradient))
        image = Image.blend(color, self.background, alpha = .4)

        # Вставка карт
        for i, card in enumerate(cards):
            position = (x + i * (x + card.size[0]), y)
            image.paste(card, position)

        return image, nums

    @staticmethod
    async def get_buffered_image(image: Image.Image) -> BytesIO:
        """Асинхронное преобразование изображения в буфер"""
        buffer = BytesIO()
        await asyncio.get_event_loop().run_in_executor(
            image_thread_pool,
            lambda: image.save(buffer, format = 'PNG', optimize = True)
        )
        buffer.seek(0)
        return buffer


# Обновленный обработчик сообщений
triplet_handler = TripletCardHandler()


@router.message(F.text.lower().startswith("триплет"))
@typing_animation_decorator(initial_message = "Раскладываю")
async def get_image_triplet(message: types.Message, bot: Bot):
    # Инициализация обработчика при первом использовании
    await triplet_handler.initialize()

    # Получение текста запроса
    text = ' '.join(message.text.split(" ")[1:])

    # Параллельное получение изображения и создание клавиатуры
    image_task = triplet_handler.get_image_three_cards(message.from_user.id)
    image, nums = await image_task

    # Обработка изображения и добавление текста
    date = pendulum.today('Europe/Kiev').format('DD.MM')
    image = await triplet_handler.process_image(
        image, text, message.from_user.first_name, date
    )

    # Параллельное создание клавиатуры и буфера изображения
    keyboard_task = create_keyboard_dops(nums, [1, 1, 1])
    buffer_task = triplet_handler.get_buffered_image(image)

    keyboard = await keyboard_task
    keyboard = await create_gpt_keyboard(keyboard, nums)
    buffer = await buffer_task

    # Отправка сообщения
    await bot.send_photo(
        message.chat.id,
        photo = BufferedInputFile(buffer.getvalue(), "image.png"),
        reply_markup = InlineKeyboardMarkup(inline_keyboard = keyboard),
        reply_to_message_id = await get_reply_message(message)
    )
