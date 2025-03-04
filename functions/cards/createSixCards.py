from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import execute_query

from PIL import Image, ImageDraw, ImageFilter
import textwrap
import numpy as np
from functions.cards.create import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread,\
    get_random_num,\
    get_colors_background, text_size, get_buffered_image
from constants import FONT_S
from functions.messages.messages import get_reply_message


async def create_meaning_keyboard(theme):
    if theme == 'недели':
        theme = "week"
    elif theme == 'месяца':
        theme = "month"

    buttons = [
        [InlineKeyboardButton(text = "Трактовка", callback_data = f"get_time_spread_meaning_{theme}")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    return keyboard


async def send_image_six_cards(bot, message, username, image, theme=None):
    para = textwrap.wrap(f"for {username}", width = 30)
    current_h, pad = 1050, 10
    draw_text = ImageDraw.Draw(image)
    for line in para:
        w, h = text_size(line, FONT_S)
        draw_text.text(((1910 - w) / 2, current_h), line, font = FONT_S)
        current_h += h + 110

    msg = await bot.send_photo(message.chat.id, photo = await get_buffered_image(image),
                               reply_to_message_id = await get_reply_message(message),
                               reply_markup = await create_meaning_keyboard(theme) if await get_choice_spread(
                                   message.reply_to_message.from_user.id) == 'raider' else None)
    file_id = msg.photo[-1].file_id

    if theme is not None:
        if theme == 'недели':
            theme = "week"
        elif theme == 'месяца':
            theme = "month"

        table = f"spreads_{theme}"
        await execute_query(f"UPDATE {table} SET file_id = $1 WHERE user_id = $2",
                            (file_id, message.reply_to_message.from_user.id,
                             ))


async def create_image_six_cards(user_id, theme=None):
    choice = await get_choice_spread(user_id)
    num = await get_random_num(choice, 8, user_id)
    card_paths = [await get_path_cards(choice, num[i]) for i in range(8)]

    parameters = {
        'deviantmoon': {'w': 250, 'h': 450, 'x': 60, 'l': 22, 'll': 5, 'p': 110},
        'manara': {'w': 250, 'h': 450, 'x': 60, 'l': 22, 'll': 5, 'p': 110},
        'magicalforest': {'w': 280, 'h': 450, 'x': 60, 'l': 0, 'll': 0, 'p': 85},
        'wildwood': {'w': 280, 'h': 450, 'x': 60, 'l': 0, 'll': 0, 'p': 85}
    }
    params = parameters.get(choice,
                            {'w': 280, 'h': 450, 'x': 60, 'l': 0, 'll': 0, 'p': 85})
    w, h, x, l, ll, p = params.values()

    col1, col2 = await get_colors_background(choice)
    color = np.random.randint(col1, col2, size = 6)
    array = get_gradient_3d(1920, 1080, (color[0], color[1], color[2]), (color[3], color[4], color[5]),
                            (True, False, True))
    image = Image.fromarray(np.uint8(array))

    background_path = await get_path_background()
    background = Image.open(background_path)
    background = background.resize((1920, 1080))
    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(image, background, alpha = .3)

    if theme is not None:
        if theme == 'недели':
            theme = "week"
        elif theme == 'месяца':
            theme = "month"

        table = f"spreads_{theme}"
        await execute_query(
            f"insert into {table} (p1, p2, p3, n1, n2, n3, threat, advice, user_id) "
            f"values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
            (num[0], num[1], num[2], num[3], num[4], num[5], num[6], num[7], user_id, choice))

    # if choice in ['deviantoom', 'manara']:
    card_positions = [
        (card_paths[0], 2 * p + w, x),
        (card_paths[1], 3 * p + 2 * w, x),
        (card_paths[2], 4 * p + 3 * w, x),

        (card_paths[3], 2 * p + w, 560),
        (card_paths[4], 3 * p + 2 * w, 560),
        (card_paths[5], 4 * p + 3 * w, 560),

        (card_paths[6], 5 * p + 4 * w + ll, 300),  # threat
        (card_paths[7], 100, 300)]  # advice

    for i, (card_path, x_coord, y_coord) in enumerate(card_positions):
        card = Image.open(card_path)
        card = card.resize((w, h))
        image.paste(card, (x_coord, y_coord))

    return image, num
