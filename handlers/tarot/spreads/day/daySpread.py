from aiogram import types, Router, F, Bot

from database import execute_select, execute_query
from filters.baseFilters import IsReply
from middlewares.statsUser import use_user_statistics
from tech.texts.affirmations import get_random_affirmations
from functions.messages.messages import get_reply_message, get_chat_id

from PIL import Image, ImageDraw
from PIL import ImageFilter
from random import randint
import textwrap
import pendulum
import numpy as np
from functions.cards.create import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread,\
    get_random_num,\
    get_colors_background, text_size, get_buffered_image

from constants import FONT_L, FONT_S
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.tarot.cards.cardsImage import get_card_image_with_text
from aiogram.types import InputMediaPhoto

router = Router()


async def create_day_keyboard(date, *callback_data):
    buttons = [
        [InlineKeyboardButton(text = "Доп карта", callback_data = f"day_meaning_day_card_dop_{date}"),
         InlineKeyboardButton(text = "Карта дня", callback_data = f"day_meaning_day_card_{date}"),
         InlineKeyboardButton(text = "Доп карта", callback_data = f"day_meaning_day_card_dop_1_{date}")],
        [InlineKeyboardButton(text = "Совет дня", callback_data = f"day_meaning_day_advice_{date}"),
         InlineKeyboardButton(text = "Итог дня", callback_data = f"day_meaning_day_conclusion_{date}"),
         InlineKeyboardButton(text = "Угроза дня", callback_data = f"day_meaning_day_aware_{date}")]
    ]

    if callback_data:
        for row in buttons:
            for i, button in enumerate(row):
                if button.callback_data == callback_data[0]:
                    row[i] = InlineKeyboardButton(text = "Расклад дня",
                                                  callback_data = f"day_meaning_day_spread_{date}")
                    break

    buttons.append([InlineKeyboardButton(text = "Трактовка", callback_data = f"get_day_spread_meaning_{date}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    return keyboard


@router.callback_query(IsReply(), F.data.startswith('day_meaning_'))
async def process_callback_day_meaning(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    date = call.data.split('_')[-1]
    user_id = call.from_user.id
    theme = "_".join(call.data.split('_')[2:-1])

    if theme == 'day_spread':
        media = await execute_select(
            f"select file_id from spreads_day where user_id = {user_id} and date = '{date}' ")

        media = InputMediaPhoto(media = media)
        keyboard = await create_day_keyboard(date)
        await bot.edit_message_media(chat_id = call.message.chat.id,
                                     message_id = call.message.message_id,
                                     media = media,
                                     reply_markup = keyboard)
    else:
        if 'dop' in theme:
            theme = 'day_card'

        num = await execute_select(f"select {theme} from spreads_day where user_id = {user_id} and date = '{date}' ")
        choice = await execute_select(
            f"select deck_type from spreads_day where user_id = {call.from_user.id} and date = '{date}' ")

        image, num = await get_card_image_with_text(call, theme, num, choice = choice)

        keyboard = await create_day_keyboard(date, call.data)
        await bot.edit_message_media(chat_id = call.message.chat.id,
                                     message_id = call.message.message_id,
                                     media = InputMediaPhoto(media = await get_buffered_image(image)),
                                     reply_markup = keyboard)


async def create_day_spread_image(user_id, username, date):
    affirmation_num = randint(0, 108)
    choice = await get_choice_spread(user_id)
    col1, col2 = await get_colors_background(choice)
    num = await get_random_num(choice, 6, user_id)
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


async def get_day_spread_image(bot: Bot, message: types.Message, date, user_id, username):
    reply_to_message_id = await get_reply_message(message)
    chat_id = await get_chat_id(message)

    file_id = await execute_select(
        "SELECT file_id FROM spreads_day WHERE user_id = $1 AND date = $2",
        (user_id, date)
    )

    if file_id:
        file_id = await execute_select(
            "SELECT file_id FROM spreads_day WHERE user_id = $1 AND date = $2",
            (user_id, date)
        )

        choice = await execute_select(
            f"select deck_type from spreads_day where user_id = {user_id} and date = '{date}' ")

        if choice == 'raider':
            keyboard = await create_day_keyboard(date)
            await bot.send_photo(chat_id, photo = file_id,
                                 reply_to_message_id = reply_to_message_id, reply_markup = keyboard)

        else:
            await bot.send_photo(chat_id, photo = file_id,
                                 reply_to_message_id = reply_to_message_id)

    else:
        image, cards, affirmation_num = await create_day_spread_image(user_id, username, date)

        choice = await get_choice_spread(user_id)

        if choice == 'raider':
            keyboard = await create_day_keyboard(date)
            msg = await bot.send_photo(chat_id, photo = await get_buffered_image(image),
                                       reply_to_message_id = reply_to_message_id, reply_markup = keyboard)
        else:
            msg = await bot.send_photo(chat_id, photo = await get_buffered_image(image),
                                       reply_to_message_id = reply_to_message_id)

        file_id = msg.photo[-1].file_id
        await execute_query(
            "INSERT INTO spreads_day (date, user_id, day_card, day_card_dop_1, day_card_dop,"
            " day_conclusion, day_advice, day_aware, affirmation_of_day, file_id, deck_type) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)",
            (
                date, user_id, cards[0], cards[1], cards[2], cards[3], cards[4], cards[5],
                affirmation_num,
                file_id, choice)
        )


async def tomorrow_spread(bot: Bot, message: types.Message, *spread_name):
    tomorrow = pendulum.tomorrow('Europe/Kiev').format('DD.MM')
    await get_day_spread_image(bot, message, tomorrow, message.from_user.id, message.from_user.first_name)


async def today_spread(bot: Bot, message: types.Message, *spread_name):
    date = pendulum.today('Europe/Kiev').format('DD.MM')
    await get_day_spread_image(bot, message, date, message.from_user.id, message.from_user.first_name)


@router.callback_query(IsReply(), F.data.startswith('today_spread'))
@use_user_statistics
async def process_callback_today_spread(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    date = pendulum.today('Europe/Kiev').format('DD.MM')
    await get_day_spread_image(bot, call.message, date, call.from_user.id, call.from_user.first_name)


@router.callback_query(IsReply(), F.data.startswith('tomorrow_spread'))
@use_user_statistics
async def process_callback_tomorrow_spread(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    tomorrow = pendulum.tomorrow('Europe/Kiev').format('DD.MM')
    await get_day_spread_image(bot, call.message, tomorrow, call.from_user.id, call.from_user.first_name)
