import asyncio
import numpy as np
from aiogram.types import InlineKeyboardMarkup

from functions.createImage import get_choice_spread, get_colors_background, get_gradient_3d,\
    get_path_background, get_path_cards, get_random_num, text_size, get_buffered_image

# from handlers.tarot.getDops import create_keyboard_dops, clear_dop_nums
from main import bot
from PIL import Image
from PIL import ImageFilter
import textwrap
import pendulum
from constants import FONT_S, FONT_L
from PIL import ImageDraw


async def get_image_three_cards(user_id):
    choice = await get_choice_spread(user_id)

    col1, col2 = await get_colors_background(choice)

    if choice == 'deviantmoon' or choice == 'manara' or choice == 'aftertarot':
        x = 140
    elif choice == "vikaoracul" or choice == "vikanimaloracul":
        x = 80
    else:
        x = 105
    y = 140

    cards = np.random.randint(col1, col2, size = 6)
    array = get_gradient_3d(1920, 1080, (cards[0], cards[1], cards[2]), (cards[3], cards[4], cards[5]),
                            (True, False, True))
    color = Image.fromarray(np.uint8(array))

    num = await get_random_num(choice, 3)
    card_paths = [await get_path_cards(choice, num[i]) for i in range(3)]

    images = []
    for i, path in enumerate(card_paths):
        card = Image.open(path)
        w, h = card.size
        images.append(card)

    background_path = await get_path_background()
    background = Image.open(background_path)
    background = background.resize((1920, 1080))
    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, background, alpha = .4)

    image.paste(images[2], ((3 * x + 2 * w), y))
    image.paste(images[1], ((2 * x + w), y))
    image.paste(images[0], (x, y))

    return image, num


async def send_image_three_cards(message, username, image, nums, spread_name=None):
    from handlers.tarot.getDops import create_keyboard_dops
    from handlers.tarot.getDops import clear_dop_nums
    from handlers.tarot.getDops import create_gpt_keyboard
    date = pendulum.today('Europe/Kiev').format('DD.MM')

    draw_text = ImageDraw.Draw(image)
    draw_text.text((759, 990), 'from @ForestSpiritLi', fill = 'white', font = FONT_L)
    draw_text.text((895, 10), date, fill = 'white', font = FONT_L)
    para = textwrap.wrap(f"for {username}", width = 30)
    current_h, pad = 1040, 10
    for line in para:
        w, h = text_size(line, FONT_S)

        draw_text.text(((1910 - w) / 2, current_h), line, font = FONT_S)
        current_h += h + pad

    if spread_name is not None:

        buttons = await create_keyboard_dops(message, nums, [1, 1, 1], spread_name)
        buttons = await create_gpt_keyboard(buttons, nums)
        keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    else:
        buttons = await create_keyboard_dops(message, nums, [1, 1, 1])
        buttons = await create_gpt_keyboard(buttons, nums)
        keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    # if message.from_user.id == ADMIN_ID:
    #     gpt_button = [
    #         [InlineKeyboardButton(text = "Трактовка Леса", callback_data = f"gpt_{nums[0]}_{nums[1]}_{nums[2]}")],
    #
    #     ]
    #
    #     keyboard.add(gpt_button)

    if message.text.lower().startswith("триплет"):
        reply_to_message_id = message.message_id
    else:
        reply_to_message_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
    msg = await bot.send_photo(message.chat.id,
                               photo = await get_buffered_image(image),
                               reply_markup = keyboard,
                               reply_to_message_id = reply_to_message_id)
    await asyncio.sleep(200)

    await clear_dop_nums(msg.message_id)
    try:
        await bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = msg.message_id, reply_markup = None)
    except:
        pass
