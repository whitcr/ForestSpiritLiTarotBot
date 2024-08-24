from aiogram import types
from PIL import Image, ImageDraw
from PIL import ImageFilter
from io import BytesIO
import numpy as np
import textwrap
from constants import FONT_XL, FONT_L
from database import execute_select
from functions.cards.create import get_choice_spread, get_random_num, get_path_cards, get_gradient_3d,\
    get_path_background, text_size

NAME_MAP = {
    'day_aware': 'Угроза дня',
    'day_conclusion': 'Итог лня',
    'day_advice': 'Совет дня',
    'day_card': 'Карта дня',
    'advice': 'Совет',
    'yesno': 'Ответ',
}


async def set_card_image(message: types.Message, theme):
    try:
        image, num = await get_card_image_with_text(message, theme)
        await send_card_image(message, image, num)
    except:
        choice = await get_choice_spread(message.from_user.id)
        num = await get_random_num(choice, 1, message.from_user.id)
        sticker_id = await execute_select("select {} from stickers where number={};", (choice, num))

        await message.bot.send_sticker(message.chat.id, sticker = sticker_id, reply_to_message_id = message.message_id)


async def set_days_card_image(message: types.Message, theme, date):
    try:
        choice = await execute_select(
            f"select deck_type from spreads_day where user_id = {message.from_user.id} and date = '{date}' ")

        num = await execute_select(
            f"select {theme} from spreads_day where user_id = {message.from_user.id} and date = '{date}' ")

        if choice == 'raider':
            image, num = await get_card_image_with_text(message, theme, num)
            await send_card_image(message, image, num)
        else:
            sticker_id = await execute_select("select {} from stickers where number={};", (choice, num))
            await message.bot.send_sticker(message.chat.id, sticker = sticker_id,
                                           reply_to_message_id = message.message_id)
    except:
        await message.reply(text = "— Сгенерируйте сначала свой расклад дня, а после смотрите значения карт.")


async def get_card_image_with_text(message, theme, *num, choice=None):
    user_id = message.from_user.id
    if choice is not None:
        choice = choice
    else:
        choice = await get_choice_spread(user_id)
    if not num:
        num = await get_random_num(choice, 1, user_id)
    else:
        num = int(num[0])
    if choice == 'raider':
        card_paths = await get_path_cards(choice, num)
        text = await execute_select(f"select {theme} from meaning_raider where number = {num};")

        color = np.random.randint(0, 108, size = 6)
        array = get_gradient_3d(1920, 1080, (color[0], color[1], color[2]), (color[3], color[4], color[5]),
                                (True, False, True))
        image = Image.fromarray(np.uint8(array))

        background = await get_path_background()
        background = Image.open(background)
        background = background.resize((1920, 1080))
        background = background.filter(ImageFilter.GaussianBlur(radius = 3))
        image = Image.blend(image, background, alpha = .2)

        temp = Image.open(card_paths)
        card = temp.resize((500, 850))
        image.paste(card, (100, 100))
        draw = ImageDraw.Draw(image)
        para = textwrap.wrap(text, width = 50)
        if len(text) > 370:
            current_h, pad = 240, 15
            font = FONT_L
        elif len(text) > 370:
            current_h, pad = 220, 10
            font = FONT_L
        elif len(text) > 500:
            current_h, pad = 200, 2
            font = FONT_L
        elif len(text) < 370:
            current_h, pad = 350, 15
            font = FONT_XL
        else:
            current_h, pad = 180, 5
            font = FONT_L

        for line in para:
            w, h = text_size(line, font)
            draw.text(((2520 - w) / 2, current_h), line, font = font)
            current_h += h + pad

        name = NAME_MAP[theme]
        text = f'{name} для тебя'
        para = textwrap.wrap(text, width = 30)
        for line in para:
            current_h, pad = 100, 10
            w, h = text_size(line, FONT_XL)
            draw.text(((2520 - w) / 2, current_h), line, font = FONT_XL)
            current_h += h + pad

        draw.text((120, 990), 'from @ForestSpiritLi', font = FONT_XL, fill = 'white')

        return image, num


async def send_card_image(message, image):
    try:
        bio = BytesIO()
        bio.name = 'image.jpeg'
        with bio:
            image.save(bio, 'JPEG')
            bio.seek(0)
            reply_to_message_id = message.message_id
            await message.bot.send_photo(message.chat.id, photo = bio, reply_to_message_id = reply_to_message_id)

    except:
        pass
