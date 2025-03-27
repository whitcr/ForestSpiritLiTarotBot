from constants import FONT_L
import random
from PIL import Image, ImageDraw
import textwrap
from aiogram.types import InputFile
from database import execute_select
from functions.cards.create import get_random_num, get_path_cards, get_buffered_image, text_size


async def practice_choose_card_post(bot, channel_id, admin_id):
    choice = "raider"
    w, h, x, y, col1, col2 = 480, 830, 124, 140, 0, 100

    image = Image.new('RGB', (1920, 1080), color = 'white')

    num = await get_random_num(choice, 3)
    card_paths = [await get_path_cards(choice, num[i]) for i in range(3)]
    images = []
    for i, path in enumerate(card_paths):
        path = Image.open(path).resize((w, h))
        images.append(path)
    image.paste(images[2], ((3 * x + 2 * w), y))
    image.paste(images[1], ((2 * x + w), y))
    image.paste(images[0], (x, y))

    card = random.choice(num)
    card = await execute_select("select name from cards where number = $1;" % (card))

    draw_text = ImageDraw.Draw(image)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    image.save("card_answer.jpg")

    text = f" Ответ на практику"
    await bot.send_photo(admin_id, photo = await get_buffered_image(image), caption = text)

    para = textwrap.wrap(f'Найдите карту {card}', width = 30)
    current_h, pad = 50, 10
    for line in para:
        w, h = text_size(line, FONT_L)
        draw_text.text(((1920 - w) / 2, current_h), line, font = FONT_L, fill = 'black')
        current_h += h + pad

    card_back = Image.open('./images/cards/raider/back.jpg')
    card_back = card_back.resize((w, h))

    image.paste(card_back, ((3 * x + 2 * w), y))
    image.paste(card_back, ((2 * x + w), y))
    image.paste(card_back, (x, y))

    text = f" — Время практики! Сосредоточьтесь и почувстуйте энергию карты {card}."
    await bot.send_photo(channel_id, photo = await get_buffered_image(image), caption = text)


async def practice_choose_card_post_answer(bot, channel_id):
    photo = InputFile("card_answer.jpg")
    text = f" —  Ответ к практике."
    await bot.send_photo(channel_id, photo = photo, caption = text)
