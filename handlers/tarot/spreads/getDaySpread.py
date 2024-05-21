from aiogram import types, Router, F

from database import execute_select, execute_query
from handlers.other.affirmations import get_random_affirmations
from main import dp, bot
from PIL import Image, ImageDraw
from PIL import ImageFilter
from random import randint
import textwrap
import pendulum
import numpy as np
from functions.createImage import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread,\
    get_random_num,\
    get_colors_background, text_size

from constants import FONT_L, FONT_S
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from handlers.tarot.getCardsImage import get_card_image_with_text
from aiogram.types import InputMediaPhoto
from io import BytesIO
import asyncio

router = Router()


async def create_day_keyboard(date, *callback_data):
    buttons = [
        InlineKeyboardButton(text = "Доп карта", callback_data = f"day_meaning_day_card_dop_{date}"),
        InlineKeyboardButton(text = "Карта дня", callback_data = f"day_meaning_day_card_{date}"),
        InlineKeyboardButton(text = "Доп карта", callback_data = f"day_meaning_day_card_dop_1_{date}"),
        InlineKeyboardButton(text = "Совет дня", callback_data = f"day_meaning_day_advice_{date}"),
        InlineKeyboardButton(text = "Итог дня", callback_data = f"day_meaning_day_conclusion_{date}"),
        InlineKeyboardButton(text = "Угроза дня", callback_data = f"day_meaning_day_aware_{date}")

    ]

    if callback_data:
        for i, button in enumerate(buttons):
            if button.callback_data == callback_data[0]:
                spread_day = InlineKeyboardButton(text = "Расклад дня",
                                                  callback_data = f"day_meaning_day_spread_{date}")
                buttons[i] = spread_day
                break

    keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 3)
    keyboard.add(*buttons)

    return keyboard


@router.callback_query(F.data.startswith('day_meaning_'))
async def process_callback_day_meaning(call: types.CallbackQuery):
    await call.answer()
    date = call.data.split('_')[-1]
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        user_id = call.from_user.id
        theme = "_".join(call.data.split('_')[2:-1])
        if theme == 'day_spread':
            media = execute_select(f"select file_id from spreads_day where user_id = {user_id} and date = '{date}' ")

            media = InputMediaPhoto(media = media)
            keyboard = await create_day_keyboard(date)
            await bot.edit_message_media(chat_id = call.message.chat.id,
                                         message_id = call.message.message_id,
                                         media = media,
                                         reply_markup = keyboard)
        else:
            media = execute_select(f"select {theme} from spreads_day where user_id = {user_id} and date = '{date}' ")

            if 'dop' in theme:
                theme = 'day_card'

            choice = execute_select(
                f"select deck_type from spreads_day where user_id = {call.from_user.id} and date = '{date}' ")

            image, num = await get_card_image_with_text(call, theme, num, choice = choice)

            bio = BytesIO()
            bio.name = 'image.jpeg'
            with bio:
                image.save(bio, 'JPEG')
                bio.seek(0)

                media = InputMediaPhoto(media = bio)

                keyboard = await create_day_keyboard(date, call.data)
                await bot.edit_message_media(chat_id = call.message.chat.id,
                                             message_id = call.message.message_id,
                                             media = media,
                                             reply_markup = keyboard)


async def create_day_spread_image(user_id, username, date):
    affirmation_num = randint(0, 108)
    choice = await get_choice_spread(user_id)
    col1, col2 = await get_colors_background(choice)
    num = await get_random_num(choice, 6)
    cards_paths = [await get_path_cards(choice, num[i]) for i in range(6)]
    color_num = np.random.randint(col1, col2, size = 6)
    array = get_gradient_3d(1920, 1080, color_num[:3], color_num[3:], (True, False, True))
    image = Image.fromarray(np.uint8(array))

    background_path = await get_path_background()
    background = Image.open(background_path).resize((1920, 1080)).filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(image, background, alpha = .3)

    width, height = 1920, 1080
    card_positions = [
        ((width // 2) - (350 // 2), (height // 2 - 250) + 100),  # card 0
        ((4 * 80 + 2 * 280 + 350) - 25, 400),  # card 1
        ((2 * 80 + 280, 400)),  # card 2
        ((width // 2) - (200 // 2) + 10, 50),  # card 3
        (90, 100),  # card 4
        ((5 * 80 + 3 * 280 + 350) - 25, 100)  # card 5
    ]

    for i, position in enumerate(card_positions):
        card = Image.open(cards_paths[i])
        size = (350, 570) if i == 0 else (280, 450) if i in (1, 2, 5, 4) else (180, 300)
        card = card.resize(size)
        image.paste(card, position)

    draw_text = ImageDraw.Draw(image)

    affirmations = await get_random_affirmations(1)
    para = textwrap.wrap(affirmations[0], width = 30)
    current_h, pad = 900, 10
    for line in para:
        w, h = text_size(line, FONT_L)
        draw_text.text(((750 - w) / 2, current_h), line, font = FONT_L)
        current_h += h + pad

    text_positions = [
        ((135, 40), 'Совет Дня', FONT_L),
        ((915, 20), 'Итог Дня', FONT_S),
        ((1600, 40), 'Угроза дня', FONT_L),
        ((485, 345), 'Доп карта', FONT_L),
        ((1255, 345), 'Доп карта', FONT_L),
        ((870, 970), 'Карта Дня', FONT_L),
        ((935, 1025), date, FONT_L),
        ((1295, 940), 'from ForestSpiritLi', FONT_L)
    ]

    for position, text, font in text_positions:
        draw_text.text(position, text, font = font, fill = 'white')

    para = textwrap.wrap(f"for {username}", width = 30)
    current_h, pad = 920, 10
    draw_text = ImageDraw.Draw(image)
    for line in para:
        w, h = text_size(line, FONT_S)
        draw_text.text(((2970 - w) / 2, current_h), line, font = FONT_S)
        current_h += h + 110

    return image, num, affirmation_num


async def get_day_spread_image(message: types.Message, date):
    try:
        file_id = execute_select(
            "SELECT file_id FROM spreads_day WHERE user_id = %s AND date = %s",
            (message.from_user.id, date)
        )

        try:
            reply_to_message_id = message.message_id
            chat_id = message.chat.id
        except:
            reply_to_message_id = message.message.reply_to_message.message_id
            chat_id = message.message.chat.id
        choice = execute_select(
            f"select deck_type from spreads_day where user_id = {message.from_user.id} and date = '{date}' ")

        if choice == 'raider':
            keyboard = await create_day_keyboard(date)
            msg = await bot.send_photo(chat_id, photo = file_id,
                                       reply_to_message_id = reply_to_message_id, reply_markup = keyboard)
            await asyncio.sleep(200)
            try:
                await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = msg.message_id,
                                                    reply_markup = None)
            except:
                pass
        else:
            await bot.send_photo(chat_id, photo = file_id,
                                 reply_to_message_id = reply_to_message_id)

    except:
        image, cards, affirmation_num = await create_day_spread_image(message.from_user.id,
                                                                      message.from_user.first_name, date)
        bio = BytesIO()
        bio.name = 'image.jpeg'
        with bio:
            image.save(bio, 'JPEG')
            bio.seek(0)
            try:
                reply_to_message_id = message.message.reply_to_message.message_id
                chat_id = message.message.chat.id
            except:
                reply_to_message_id = message.message_id
                chat_id = message.chat.id

            choice = await get_choice_spread(message.from_user.id)
            if choice == 'raider':
                keyboard = await create_day_keyboard(date)
                msg = await bot.send_photo(chat_id, photo = FSInputFile(bio),
                                           reply_to_message_id = reply_to_message_id, reply_markup = keyboard)
            else:
                msg = await bot.send_photo(chat_id, photo = FSInputFile(bio),
                                           reply_to_message_id = reply_to_message_id)
            choice = await get_choice_spread(message.from_user.id)
            file_id = msg.photo[-1].file_id

            execute_query(
                "INSERT INTO spreads_day (date, user_id, day_card, day_card_dop_1, day_card_dop,"
                " day_conclusion, day_advice, day_aware, affirmation_of_day, file_id, deck_type) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    date, message.from_user.id, cards[0], cards[1], cards[2], cards[3], cards[4], cards[5],
                    affirmation_num,
                    file_id, choice)
            )

            await asyncio.sleep(200)
            try:
                await bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = msg.message_id,
                                                    reply_markup = None)
            except:
                pass


async def tomorrow_spread(message: types.Message, *spread_name):
    tomorrow = pendulum.tomorrow('Europe/Kiev').format('DD.MM')
    await get_day_spread_image(message, tomorrow)


async def today_spread(message: types.Message, *spread_name):
    date = pendulum.today('Europe/Kiev').format('DD.MM')
    await get_day_spread_image(message, date)
