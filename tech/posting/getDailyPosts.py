from constants import FONT_L
from bot import dp, bot, cursor, db
import random
from random import randint
from PIL import Image, ImageDraw
from PIL import ImageFilter
from io import BytesIO
import textwrap
import asyncio
import numpy as np
from aiogram import types
from functions import get_path_cards, get_path_background, get_gradient_3d, get_random_num
from handlers.other.affirmations import get_random_affirmations
from other.phrases import get_random_phrases
from constants import P_FONT_L, P_FONT_XL, P_FONT_S
from aiogram.dispatcher.filters import IDFilter
from constants import ADMIN_ID, CHANNEL_ID
from handlers.astrology.getMoon import get_moon_today
from chatGPT.getGPT import get_text_energy_day
from aiogram.types import InputFile
from aiogram.utils.markdown import hlink


async def get_post_template():
    background_path = await get_path_background()

    color = Image.open('./images/tech/design_posts/backcolor.png').convert("RGBA")
    front = Image.open('./images/tech/design_posts/front.png').convert("RGBA")

    background = Image.open(background_path).convert("RGBA")
    background = background.resize((1920, 1080))

    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, background, alpha = .2)
    image.paste(front, (0, 0), front)

    return image


# @dp.message_handler(lambda message: message.text.lower() == "тест")
async def get_statistic_post():
    asyncio.create_task(send_statistic_post())


async def send_statistic_post():
    image = await get_post_template()
    files = []
    quantities = []
    cards_name = []

    for i in range(3):
        cursor.execute("select card from statistic_cards ORDER BY quantity DESC LIMIT 1")
        card = cursor.fetchone()[0]
        cursor.execute("select name from cards where number={};".format(card))
        name = cursor.fetchone()[0]
        cursor.execute("select quantity from statistic_cards where card = '{}'".format(card))
        quantity = cursor.fetchone()[0]
        file = await get_path_cards('raider', int(card))
        cursor.execute("delete from statistic_cards where card = '{}'".format(card))
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

    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    text_energy = await get_text_energy_day(cards_name)
    text = f"<b>Энергии сегодняшнего дня </b>\n\n<b>Вот такие вот Арканы преследовали нас сегодня. "\
           f"Как прошел ваш день? Есть ли какие-то соответствия? "\
           f"Какие ваши мысли в целом об этом дне и как могли бы данные карты проиграться?</b>"\
           f"\n\n"\
           f"Также можете посмотреть, как пройдет ваш завтрашний день с помощью команды <b>'расклад на завтра'</b>."

    post = await bot.send_photo(CHANNEL_ID, photo = bio, caption = text)
    await bot.send_message(CHANNEL_ID, text = text_energy, reply_to_message_id = post.message_id)


text_temp = []


async def moon_posting():
    moon_zodiac_name, moon_phase, moon_day, moon_visibility = await get_moon_today()

    text = f"{moon_phase}                          \n\nЗнак: {moon_zodiac_name}                 \n\n{moon_visibility}"
    current_h, pad = 350, 65

    if int(moon_day) == 22:
        num = 0;
    elif int(moon_day) > 22:
        num = int(moon_day) - 22
    else:
        num = int(moon_day)
    cursor.execute("select name from cards where number={};".format(num))
    day_arcane = cursor.fetchone()[0]
    cursor.execute("select day_advice from meaning_raider where number={};".format(num))
    day_advice = cursor.fetchone()[0]
    cursor.execute("select text from moon_days where day={};".format(moon_day))
    moon_day_text = cursor.fetchone()[0]
    moon_day = moon_day

    return text, day_arcane, day_advice, moon_day, moon_day_text, current_h, pad


@dp.callback_query_handler((IDFilter(user_id = ADMIN_ID)), lambda call: call.data == 'morning_posting')
async def get_morning_posting(call: types.CallbackQuery):
    await call.answer()
    await morning_posting()


async def morning_posting():
    text, day_arcane, day_advice, moon_day, moon_day_text, current_h, pad = await moon_posting()

    image = await get_post_template()

    draw = ImageDraw.Draw(image)
    draw.text((850, 15), 'СЕГОДНЯ', font = P_FONT_L, fill = 'white')

    arcane = f"Аркан дня: {day_arcane}"
    para = textwrap.wrap(arcane, width = 30)
    for line in para:
        draw.text((230, 130), f"{line}\n\n", font = P_FONT_S)

    draw.text((220, 950), f'{moon_day} лунный день', font = P_FONT_L, fill = 'white')

    cursor.execute("SELECT number FROM meaning_raider WHERE name = %s;", (day_arcane.lower(),))
    num = cursor.fetchone()[0]

    card_path = await get_path_cards('raider', num)
    card_path = Image.open(card_path)
    card_path = card_path.resize((450, 730))
    image.paste(card_path, (200, 200))

    para = textwrap.wrap(text, width = 20)
    for line in para:
        w, h = text_size(line, FONT_L)
        draw.text(((2200 - w) / 2, current_h), f"{line}\n\n", font = P_FONT_XL)
        current_h += h + pad

    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)

    affirmations = await get_random_affirmations(2)

    day_affirmations = f"— <i>{affirmations[0]}\n\n— {affirmations[1]}</i>\n"

    phrase = await get_random_phrases(1)

    text = f"<b><u>Аркан дня: {day_arcane}</u></b>\n{day_advice}\n\n<b><u>{moon_day} лунный день</u></b>\n{moon_day_text}<b><u>Аффирмации дня</u></b>"\
           f"\n{day_affirmations}\n<b><u>Совет от Ли</u></b>\n{phrase[0]}\n\n—  Не забываем писать в комментариях <b>'Расклад дня'</b>, чтобы получить персональный прогноз на день от Ли!"

    await bot.send_photo(CHANNEL_ID, bio, caption = text)


async def notify_week_spread():
    message = f" — Пишем <b>'расклад на неделю'</b> в комментариях и узнаем, чего опасаться и чего ждать в следующие семь дней. Чем больше реакций, тем лучше карты <3"
    await bot.send_message(CHANNEL_ID, message)


async def practice_quiz_post():
    numbers = random.sample(range(0, 74), 3)
    for num in numbers:
        cursor.execute("select practice.name from practice where number = {}".format(num))
        card = cursor.fetchone()[0]
        cursor.execute("select quiz_02 from practice where number = {}".format(num))
        correct_answer = cursor.fetchone()[0]

        false = random.sample(range(0, 74), 4)
        if num in false:
            false = random.sample(range(0, 74), 4)

        answers = []
        for el in false:
            cursor.execute("select quiz_02 from practice where number = {}".format(el))
            false_answer = cursor.fetchone()[0]
            answers.append(false_answer)
        answers.append(correct_answer)
        random.shuffle(answers)

        c = await check_correct_answer(answers, correct_answer)

        await bot.send_poll(CHANNEL_ID, f'Какое значение может быть у карты {card}?',
                            [f'{answers[0]}', f'{answers[1]}', f'{answers[2]}', f'{answers[3]}', f'{answers[4]}'],
                            type = 'quiz', correct_option_id = c)


async def check_correct_answer(answers, correct_answer):
    x = 0
    for el in answers:
        x = x + 1
        if el == correct_answer:
            c = x - 1
            return c


async def practice_choose_card_post():
    num = random.sample(range(0, 22), 3)
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
    cursor.execute("select name from cards where number = %f   ;" % (card))
    card = cursor.fetchone()[0]

    draw_text = ImageDraw.Draw(image)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    image.save("card_answer.jpg")

    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'JPEG')
        bio.seek(0)
        text = f" Ответ на практику"
        await bot.send_photo(ADMIN_ID, photo = bio, caption = text)

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

    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'JPEG')
        bio.seek(0)
        text = f" — Время практики! Сосредоточьтесь и почувстуйте энергию карты {card}."
        await bot.send_photo(CHANNEL_ID, photo = bio, caption = text)


async def practice_choose_card_post_answer():
    photo = InputFile("card_answer.jpg")
    text = f" —  Ответ к практике."
    await bot.send_photo(CHANNEL_ID, photo = photo, caption = text)


async def history_image():
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
    cursor.execute("UPDATE posting SET file_id ='{}' where post = 'history'".format(file_id))
    db.commit()


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

    color = Image.open('./images/tech/design_posts/backcolor.png').convert("RGBA")
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


async def get_meditation_post():
    number = randint(1, 15)
    cursor.execute("select name from meditation_text where number={}".format(number))
    name = cursor.fetchone()[0]
    cursor.execute("select text from meditation_text where number = {}".format(number))
    text = cursor.fetchone()[0]

    rules = hlink('Как медитировать?', 'https://telegra.ph/Pravila-Meditacii-10-16')

    text = f"<b>ВОСКРЕСНАЯ МЕДИТАЦИЯ \n\n {name}</b>\n\n{text}\n\n"\
           f"{rules}"\
           f"\n\n— Делимся впечатлениями от медитации в комментариях!"

    await bot.send_message(CHANNEL_ID, text = text)
