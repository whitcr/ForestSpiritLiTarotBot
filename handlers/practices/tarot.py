from aiogram import types, Router, F, Bot
from aiogram.types import BufferedInputFile

from database import execute_select
from PIL import Image, ImageDraw
from io import BytesIO
from random import randint
import textwrap
import random
import keyboard as kb
from filters.baseFilters import IsReply
from functions.cards.create import get_path_cards, get_choice_spread, get_random_num, text_size
from handlers.tarot.spreads.getSpreads import get_image_three_cards
from constants import FONT_L

router = Router()


@router.callback_query(IsReply(), F.data == 'practice_menu_tarot')
async def practice_menu_tarot(bot: Bot, call: types.CallbackQuery):
    await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                text = f"<b>Карта</b> — вы должны будете почувствовать скрытую карту.\n\n"
                                       f"<b>Выбор карты</b> — вам надо будет почувствовать определенную карту.\n\n"
                                       f"<b>Триплет</b> — трактовка карт на заданную тему.\n\n"
                                       f"<b>История</b> — трактовка карт в виде истории.\n\n"
                                       f"<b>Викторина</b> — вопросы о значениях карт",
                                reply_markup = kb.practice_menu_tarot_keyboard)


@router.callback_query(IsReply(), F.data == 'practice_triple')
async def practice_triple(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)

    image, num = await get_image_three_cards(call.from_user.id)

    num = randint(0, 14)
    text = await execute_select("select questions from practice where number = $1;", (num,))

    draw_text = ImageDraw.Draw(image)
    text = textwrap.wrap(text, width = 30)

    current_h, pad = 80, 10
    for line in text:
        w, h = text_size(line, FONT_L)
        draw_text.text(((1920 - w) / 2, current_h), line, font = FONT_L)
        current_h += h + pad

    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'white')
    draw_text.text((770, 20), 'Трактовка триплета', font = FONT_L, fill = 'white')

    bio = BytesIO()
    bio.name = 'image.jpeg'
    image.save(bio, 'JPEG')
    bio.seek(0)

    text = "Трактуйте карты на заданную тему. \n<code>Спорьте, рассуждайте, думайте, ответов не будет.</code>"
    await bot.send_photo(call.message.chat.id, photo = bio, caption = text)


@router.callback_query(IsReply(), F.data == 'practice_card')
async def practice_card(bot: Bot, call: types.CallbackQuery, state="*"):
    await call.answer()
    await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)

    image_card = Image.new('RGB', (1920, 1080), color = 'white')
    choice = await get_choice_spread(call.from_user.id)
    num = await get_random_num(choice, 1, call.from_user.id)
    card_paths = await get_path_cards(choice, num)

    card = Image.open(card_paths)
    card = card.resize((520, 850))
    image_card.paste(card, (700, 100))

    draw_text = ImageDraw.Draw(image_card)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    image_card_save = BytesIO()
    image_card_save.name = 'image_card.jpeg'
    image_card.save(image_card_save, 'JPEG')
    image_card_save.seek(0)

    async with state.proxy() as data:
        data['image_card'] = image_card_save

    card_back = Image.open('./cards/cards/raider/back.jpg')
    card_back = card_back.resize((520, 850))
    image_card.paste(card_back, (700, 100))

    draw_text = ImageDraw.Draw(image_card)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')
    draw_text.text((698, 20), 'Какую карту вы чувствуете?', font = FONT_L, fill = 'black')

    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image_card.save(bio, 'JPEG')
        bio.seek(0)
        text = "Сосредоточьтесь и почувстуйте энергию, исходящую от картинки.\n<code>При вызове нового задания ответ прошлого будет утерян, \nответ может узнать только тот, кто взял задание. </code>"
        await bot.send_photo(call.message.chat.id, photo = BufferedInputFile(bio), caption = text,
                             reply_markup = kb.practice_card_keyboard)


@router.callback_query(IsReply(), F.data == 'practice_choose_card')
async def practice_choose_card(bot: Bot, call: types.CallbackQuery, state="*"):
    await call.answer()
    await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)

    choice = await get_choice_spread(call.from_user.id)

    if choice == 'deviantmoon' or choice == 'manara' or choice == 'aftertarot':
        w, h, x, y, col1, col2 = 450, 830, 143, 140, 0, 80
    elif choice == 'aftertarot':
        w, h, x, y, col1, col2 = 450, 830, 143, 140, 20, 200
    elif choice == 'magicalforest' or choice == 'wildwood':
        w, h, x, y, col1, col2 = 500, 830, 105, 140, 0, 200
    elif choice == "vikaoracul" or choice == "vikanimaloracul":
        w, h, x, y, col1, col2 = 530, 830, 77, 140, 0, 50
    elif choice == "raider":
        w, h, x, y, col1, col2 = 480, 830, 124, 140, 0, 100
    else:
        w, h, x, y, col1, col2 = 500, 830, 105, 140, 0, 150

    image = Image.new('RGB', (1920, 1080), color = 'white')

    num = await get_random_num(choice, 3, call.from_user.id)
    card_paths = [await get_path_cards(choice, num[i]) for i in range(3)]
    images = []
    for i, path in enumerate(card_paths):
        path = Image.open(path).resize((w, h))
        images.append(path)
    image.paste(images[2], ((3 * x + 2 * w), y))
    image.paste(images[1], ((2 * x + w), y))
    image.paste(images[0], (x, y))

    card = random.choice(num)
    card = await execute_select("select name from cards where number = $1;", (card,))

    draw_text = ImageDraw.Draw(image)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    image_save = BytesIO()
    image_save.name = 'image_card.jpeg'
    image.save(image_save, 'JPEG')
    image_save.seek(0)

    async with state.proxy() as data:
        data['image_choose_card'] = image_save

    para = textwrap.wrap(f'Найдите карту {card}', width = 30)
    current_h, pad = 50, 10
    for line in para:
        w, h = text_size(line, FONT_L)
        draw_text.text(((1920 - w) / 2, current_h), line, font = FONT_L, fill = 'black')
        current_h += h + pad

    card_back = Image.open('./cards/cards/raider/back.jpg')
    card_back = card_back.resize((w, h))

    image.paste(card_back, ((3 * x + 2 * w), y))
    image.paste(card_back, ((2 * x + w), y))
    image.paste(card_back, (x, y))

    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'JPEG')
        bio.seek(0)
        text = f"Сосредоточьтесь и почувстуйте энергию карты {card}.\n<code>При вызове нового задания ответ прошлого будет утерян, \nответ может узнать только тот, кто взял задание. </code>"
        await bot.send_photo(call.message.chat.id, photo = BufferedInputFile(bio), caption = text,
                             reply_markup = kb.practice_choose_card_keyboard)


@router.callback_query(IsReply(), F.data == 'practice_card_answer')
async def practice_card_answer(bot: Bot, call: types.CallbackQuery, state="*"):
    await call.answer()
    try:
        async with state.proxy() as data:
            image_card = data['image_card']
            await bot.send_photo(call.message.chat.id, photo = image_card)
            data['image_card'] = None
    except:
        return 0


@router.callback_query(IsReply(), F.data == 'practice_choose_card_answer')
async def practice_card_answer(bot: Bot, call: types.CallbackQuery, state="*"):
    async with state.proxy() as data:
        image_card = data['image_choose_card']
        await bot.send_photo(call.message.chat.id, photo = image_card)
        data['image_choose_card'] = None


@router.callback_query(IsReply(), F.data == 'practice_quiz')
async def practice_quiz(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)

    numbers = random.sample(range(0, 74), 3)
    for num in numbers:
        card = await execute_select("select practice.name from practice where number = {}", (num,))

        correct_answer = await execute_select("select quiz_02 from practice where number = {}", (num,))

        false = random.sample(range(0, 74), 4)
        if num in false:
            false = random.sample(range(0, 74), 4)

        answers = []
        for el in false:
            false_answer = await execute_select("select quiz_02 from practice where number = {}", (el,))

            answers.append(false_answer)
        answers.append(correct_answer)
        random.shuffle(answers)

        c = await check_correct_answer(answers, correct_answer)

        await bot.send_poll(call.message.chat.id, f'Какое значение может быть у карты {card}?',
                            [f'{answers[0]}', f'{answers[1]}', f'{answers[2]}', f'{answers[3]}', f'{answers[4]}'],
                            type = 'quiz', correct_option_id = c, is_anonymous = False)


async def check_correct_answer(answers, correct_answer):
    x = 0
    for el in answers:
        x = x + 1
        if el == correct_answer:
            c = x - 1
            return c
