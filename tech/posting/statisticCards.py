from PIL import Image, ImageDraw
import asyncio
from constants import P_FONT_L
from database import execute_query, execute_select
from functions.gpt.requests import get_text_energy_day
from functions.cards.create import get_path_cards, get_buffered_image
from tech.posting.templates import get_post_template


async def get_statistic_post(bot, channel_id):
    image = await get_post_template()
    files = []
    quantities = []
    cards_name = []

    for i in range(3):
        card = await execute_select("select card from statistic_cards ORDER BY quantity DESC LIMIT 1")
        name = await execute_select("select name from cards where number={};", (card,))
        quantity = await execute_select("select quantity from statistic_cards where card = '{}'", (card,))
        file = await get_path_cards('raider', int(card))
        await execute_query("delete from statistic_cards where card = '{}'", (card,))
        files.append(file)
        quantities.append(quantity)
        cards_name.append(name)

    w = 500
    h = 830
    x = 105
    y = 140

    card = Image.open(files[0])
    card = card.resize((w, h))
    image.paste(card, ((2 * x + w), y))

    card = Image.open(files[1])
    card = card.resize((w - 100, h - 180))
    image.paste(card, (1350, y + 200))

    card = Image.open(files[2])
    card = card.resize((w - 100, h - 180))
    image.paste(card, (160, y + 200))

    draw_text = ImageDraw.Draw(image)
    draw_text.text((780, 15), 'ЭНЕРГИИ ДНЯ', font = P_FONT_L, fill = 'white')

    text_energy = await get_text_energy_day(cards_name)
    text = f"<b>Энергии сегодняшнего дня </b>\n\n<b>Вот такие вот Арканы преследовали нас сегодня. "\
           f"Как прошел ваш день? Есть ли какие-то соответствия? "\
           f"Какие ваши мысли в целом об этом дне и как могли бы данные карты проиграться?</b>"\
           f"\n\n"\
           f"Также можете посмотреть, как пройдет ваш завтрашний день с помощью команды <b>'расклад на завтра'</b>."

    post = await bot.send_photo(channel_id, photo = await get_buffered_image(image), caption = text)
    await bot.send_message(channel_id, text = text_energy, reply_to_message_id = post.message_id)


text_temp = []
