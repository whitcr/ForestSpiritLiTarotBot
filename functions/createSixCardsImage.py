from aiogram.types import BufferedInputFile
from main import bot
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
import textwrap
import numpy as np
from functions.createImage import get_path_cards, get_path_background, get_gradient_3d, get_choice_spread,\
    get_random_num,\
    get_colors_background, text_size
from constants import FONT_S


async def send_image_six_cards(message, username, image, theme):
    para = textwrap.wrap(f"for {username}", width = 30)
    current_h, pad = 1050, 10
    draw_text = ImageDraw.Draw(image)
    for line in para:
        w, h = text_size(line, FONT_S)
        draw_text.text(((1910 - w) / 2, current_h), line, font = FONT_S)
        current_h += h + 110

    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'JPEG')
        bio.seek(0)
        reply_to_message_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
        msg = await bot.send_photo(message.chat.id, photo = BufferedInputFile(bio),
                                   reply_to_message_id = reply_to_message_id)
        file_id = msg.photo[-1].file_id
        table = f"spreads_{theme}"
        # execute_query(
        # "insert into {} (user_id, file_id) values ('{}', '{}')".format(table, message.reply_to_message.from_user.id,
        #                                                                file_id))


async def create_image_six_cards(user_id):
    choice = await get_choice_spread(user_id)
    num = await get_random_num(choice, 8)
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

    # if choice in ['deviantoom', 'manara']:
    card_positions = [(card_paths[0], 4 * p + 3 * w, x),
                      (card_paths[1], 2 * p + w, x),
                      (card_paths[2], 3 * p + 2 * w, x),
                      (card_paths[3], 4 * p + 3 * w, 560),
                      (card_paths[4], 3 * p + 2 * w, 560),
                      (card_paths[5], 2 * p + w, 560),
                      (card_paths[6], 5 * p + 4 * w + ll, 300),
                      (card_paths[7], 100, 300)]

    for i, (card_path, x_coord, y_coord) in enumerate(card_positions):
        card = Image.open(card_path)
        card = card.resize((w, h))
        image.paste(card, (x_coord, y_coord))

    return image, num
