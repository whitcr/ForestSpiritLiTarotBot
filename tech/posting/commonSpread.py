from PIL import Image, ImageDraw, ImageFont
import textwrap
from aiogram import types, F, Router, Bot
from constants import P_FONT_L
from database import execute_select
from filters.baseFilters import IsAdmin
from functions.cards.create import get_choice_spread, get_path_cards, text_size,\
    get_buffered_image
from tech.posting.templates import get_post_template

router = Router()


@router.message(IsAdmin(), F.text.lower().startswith("!общий"))
async def get_image_common_spread(message: types.Message, bot: Bot):
    text = " ".join(message.text.split(" ")[1:]).split("-")[0]
    cards_names = message.text.split("-")[1:]

    text = " ".join(text)

    image = await get_post_template()

    cards = Image.open('./images/tech/design_posts/common_spread.png').convert("RGBA")

    image.paste(cards, (1, 1), cards)

    choice = await get_choice_spread(message.from_user.id)
    cards_path = []
    for card in cards_names:
        num = await execute_select("SELECT number FROM meaning_raider where name = $1", (card,))

        card_path = await get_path_cards(choice, num)
        cards_path.append(card_path)

    draw = ImageDraw.Draw(image)
    para = textwrap.wrap(text.upper(), width = 50)

    length = len(para)
    if length == 1:
        current_h, pad = 160, 10
        FONT = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 100)
    elif length == 2:
        current_h, pad = 140, 10
        FONT = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 80)

    for line in para:
        w, h = text_size(line, FONT)
        draw.text(((1920 - w) / 2, current_h), line, font = FONT)
        current_h += h + pad

    draw.text((735, 15), 'ОБЩИЙ РАСКЛАД', font = P_FONT_L, fill = 'white')

    await bot.send_photo(message.chat.id, photo = await get_buffered_image(image))

    w, h = 370, 620;
    x, y = 85, 333

    card = Image.open(cards_path[0])
    card = card.resize((w, h))
    image.paste(card, (x, y))

    card = Image.open(cards_path[1])
    card = card.resize((w, h))
    image.paste(card, (2 * x + w, y))

    card = Image.open(cards_path[2])
    card = card.resize((w, h))
    image.paste(card, (3 * x + 2 * w, y))

    card = Image.open(cards_path[3])
    card = card.resize((w, h))
    image.paste(card, (4 * x + 3 * w + 5, y))

    await bot.send_photo(message.chat.id, photo = await get_buffered_image(image))
