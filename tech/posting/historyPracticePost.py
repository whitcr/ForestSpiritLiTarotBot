from constants import FONT_L
import random
from PIL import Image, ImageDraw
from PIL import ImageFilter
from io import BytesIO
import numpy as np

from database import execute_query
from functions.cards.create import get_path_cards, get_gradient_3d, get_path_background


async def history_image(bot, channel_id):
    image = await get_image_history()

    draw_text = ImageDraw.Draw(image)
    draw_text.text((1320, 80), 'История', font = FONT_L, fill = 'white')
    draw_text.text((210, 80), 'Главный герой', font = FONT_L, fill = 'white')
    draw_text.text((2290, 80), 'Главное событие', font = FONT_L, fill = 'white')

    draw_text = ImageDraw.Draw(image)
    draw_text.text((1230, 20), '@ForestSpiritLi', font = FONT_L, fill = 'white')
    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    text = f"<b><u>Трактовка Истории</u></b>\n\nВам нужно растрактовать историю, которую поведали нам карты. "\
           f"Не ограничивайте себя, проявите все свои знания, главно сделайте это интересно и чтобы это подходило к значениям карт! \n\n"\
           f"<i>У каждого могут быть разные рассказы и в этом вся прелесть, не бойтесь ошибиться и не бойтесь сказать что-то не так, наоборот проявите смекалку и каплю юмора, если она будет уместна. </i> \n\n"\
           f"Первые три карты по вертикали это карты, которые описывают главного героя. "\
           f"После — карты, описывающие саму историю, их связывает некая белая полоса, которая показывает хронологический порядок событий."\
           f" И последние три карты описывают главное событие истории.\n\n"\
           f"Жду ваших замечательных историй в комментариях!"
    msg = await bot.send_photo(CHANNEL_ID, photo = bio, caption = text)
    file_id = msg.photo[-1].file_id
    await execute_query("UPDATE posting SET file_id ='{}' where post = 'history'", (file_id,))


async def get_image_history():
    num = random.sample(range(0, 78), 15)
    card = []
    for element in num:
        path = await get_path_cards("raider", element)
        card.append(path)

    w = 340
    h = 560
    x = 185
    y = 140
    col1 = 0
    col2 = 130

    cards = np.random.randint(col1, col2, size = 6)
    array = get_gradient_3d(2800, 1970, (cards[0], cards[1], cards[2]), (cards[3], cards[4], cards[5]),
                            (True, False, True))
    image = Image.fromarray(np.uint8(array))
    path = await get_path_background()

    color = Image.open('./cards/tech/design_posts/backcolor.png').convert("RGBA")
    color = color.resize((2800, 1970))
    background = Image.open(path).convert("RGBA")
    background = background.resize((2800, 1970))

    alpha = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, alpha, alpha = .3)
    draw_text = ImageDraw.Draw(image)
    draw_text.text((1000, 400), '—————————————————————————', font = FONT_L, fill = 'white')
    draw_text.text((1000, 1000), '—————————————————————————', font = FONT_L, fill = 'white')
    draw_text.text((1000, 1600), '—————————————————————————', font = FONT_L, fill = 'white')
    draw_text.text((1918, 693), '|', font = FONT_L, fill = 'white')
    draw_text.text((873, 1290), '|', font = FONT_L, fill = 'white')

    watermark = Image.open(card[14])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((5 * x + 4 * w), y + 1200))
    watermark = Image.open(card[12])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((5 * x + 4 * w), y))
    watermark = Image.open(card[13])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((5 * x + 4 * w), y + 600))

    watermark = Image.open(card[11])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((4 * x + 3 * w), y + 1200))
    watermark = Image.open(card[10])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((3 * x + 2 * w), y + 1200))
    watermark = Image.open(card[9])
    carde = watermark.resize((w, h))
    image.paste(carde, ((2 * x + w), y + 1200))
    watermark = Image.open(card[6])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((4 * x + 3 * w), y + 600))
    watermark = Image.open(card[7])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((3 * x + 2 * w), y + 600))
    watermark = Image.open(card[8])
    carde = watermark.resize((w, h))
    image.paste(carde, ((2 * x + w), y + 600))
    watermark = Image.open(card[5])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((4 * x + 3 * w), y))
    watermark = Image.open(card[4])
    cardу = watermark.resize((w, h))
    image.paste(cardу, ((3 * x + 2 * w), y))
    watermark = Image.open(card[3])
    carde = watermark.resize((w, h))
    image.paste(carde, ((2 * x + w), y))

    watermark = Image.open(card[2])
    carde = watermark.resize((w, h))
    image.paste(carde, (x, y + 1200))
    watermark = Image.open(card[1])
    carde = watermark.resize((w, h))
    image.paste(carde, (x, y + 600))
    watermark = Image.open(card[0])
    carde = watermark.resize((w, h))
    image.paste(carde, (x, y))

    return image
