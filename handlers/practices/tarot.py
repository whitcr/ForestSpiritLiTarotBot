from aiogram import types, Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import execute_select
from PIL import Image, ImageDraw
from random import randint, sample
import textwrap
import random
import keyboard as kb
from filters.baseFilters import IsReply
from functions.cards.create import (
    get_path_cards,
    get_choice_spread,
    get_random_num,
    text_size,
    get_buffered_image
)
from functions.messages.messages import typing_animation_decorator
from handlers.tarot.spreads.getSpreads import get_image_three_cards
from constants import FONT_L
from middlewares.statsUser import use_user_statistics

router = Router()


@router.callback_query(IsReply(), F.data == 'practice_menu_tarot')
async def practice_menu_tarot(call: types.CallbackQuery, bot: Bot):
    await call.message.edit_text(
        text = (
            "<b>Карта</b> — вы должны будете почувствовать скрытую карту.\n\n"
            "<b>Выбор карты</b> — вам надо будете почувствовать определенную карту.\n\n"
            "<b>Триплет</b> — трактовка карт на заданную тему.\n\n"
            "<b>История</b> — трактовка карт в виде истории.\n\n"
            "<b>Викторина</b> — вопросы о значениях карт"
        ),
        reply_markup = kb.practice_menu_tarot_keyboard
    )


@router.callback_query(IsReply(), F.data == 'practice_triple')
@use_user_statistics
async def practice_triple(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    await bot.delete_message(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id
    )

    image, _ = await get_image_three_cards(call.from_user.id)

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

    text = "Трактуйте карты на заданную тему. \n<code>Спорьте, рассуждайте, думайте, ответов не будет.</code>"
    await bot.send_photo(
        call.message.chat.id,
        photo = await get_buffered_image(image),
        caption = text
    )


@router.callback_query(IsReply(), F.data == 'practice_card')
@typing_animation_decorator(initial_message = "Создаю")
@use_user_statistics
async def practice_card(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    await bot.delete_message(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id
    )

    image_card = Image.new('RGB', (1920, 1080), color = 'white')
    choice = await get_choice_spread(call.from_user.id)
    num = await get_random_num(choice, 1, call.from_user.id)
    card_paths = await get_path_cards(choice, num)

    card = Image.open(card_paths)
    card = card.resize((520, 850))
    image_card.paste(card, (700, 100))

    draw_text = ImageDraw.Draw(image_card)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    builder = InlineKeyboardBuilder()
    builder.button(
        text = "Показать карту",
        callback_data = f"practice_card_answer:{num}"
    )

    card_back = Image.open('./images/cards/raider/back.jpg')
    card_back = card_back.resize((520, 850))
    image_card.paste(card_back, (700, 100))

    draw_text = ImageDraw.Draw(image_card)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')
    draw_text.text((698, 20), 'Какую карту вы чувствуете?', font = FONT_L, fill = 'black')

    text = "Сосредоточьтесь и почувстуйте энергию, исходящую от картинки.\n<code>При вызове нового задания ответ прошлого будет утерян, \nответ может узнать только тот, кто взял задание. </code>"
    await bot.send_photo(
        call.message.chat.id,
        photo = await get_buffered_image(image_card),
        caption = text,
        reply_markup = builder.as_markup(),
        reply_to_message_id = call.message.reply_to_message.message_id
    )


@router.callback_query(IsReply(), F.data == 'practice_choose_card')
@typing_animation_decorator(initial_message = "Создаю")
@use_user_statistics
async def practice_choose_card(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    await bot.delete_message(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id
    )

    choice = await get_choice_spread(call.from_user.id)

    deck_configs = {
        'deviantmoon': (450, 830, 143, 140, 0, 80),
        'manara': (450, 830, 143, 140, 0, 80),
        'aftertarot': (450, 830, 143, 140, 20, 200),
        'magicalforest': (500, 830, 105, 140, 0, 200),
        'wildwood': (500, 830, 105, 140, 0, 200),
        'vikaoracul': (530, 830, 77, 140, 0, 50),
        'vikanimaloracul': (530, 830, 77, 140, 0, 50),
        'raider': (480, 830, 124, 140, 0, 100)
    }

    w, h, x, y, col1, col2 = deck_configs.get(choice, (500, 830, 105, 140, 0, 150))

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
    card_name = await execute_select("select name from cards where number = $1;", (card,))

    draw_text = ImageDraw.Draw(image)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    builder = InlineKeyboardBuilder()
    builder.button(
        text = "Показать ответ",
        callback_data = f"practice_choose_card_answer:{num[0]}:{num[1]}:{num[2]}"
    )

    card_back = Image.open('./images/cards/raider/back.jpg')
    card_back = card_back.resize((w, h))

    image.paste(card_back, ((3 * x + 2 * w), y))
    image.paste(card_back, ((2 * x + w), y))
    image.paste(card_back, (x, y))

    para = textwrap.wrap(f'Найдите карту {card_name}', width = 30)
    current_h, pad = 50, 10
    for line in para:
        w, h = text_size(line, FONT_L)
        draw_text.text(((1920 - w) / 2, current_h), line, font = FONT_L, fill = 'black')
        current_h += h + pad

    text = f"Сосредоточьтесь и почувстуйте энергию карты {card_name}.\n<code>При вызове нового задания ответ прошлого будет утерян, \nответ может узнать только тот, кто взял задание. </code>"
    await bot.send_photo(
        call.message.chat.id,
        photo = await get_buffered_image(image),
        caption = text,
        reply_markup = builder.as_markup(),
        reply_to_message_id = call.message.reply_to_message.message_id
    )


@router.callback_query(IsReply(), F.data.startswith('practice_card_answer:'))
async def practice_card_answer(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    choice = await get_choice_spread(call.from_user.id)
    num = call.data.split(':')[1]
    card_paths = await get_path_cards(choice, num)

    image_card = Image.new('RGB', (1920, 1080), color = 'white')
    card = Image.open(card_paths)
    card = card.resize((520, 850))
    image_card.paste(card, (700, 100))

    draw_text = ImageDraw.Draw(image_card)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    draw_text = ImageDraw.Draw(image_card)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')
    draw_text.text((750, 20), 'Ответ', font = FONT_L, fill = 'black')

    await bot.send_photo(call.message.chat.id, photo = await get_buffered_image(image_card))


@router.callback_query(IsReply(), F.data.startswith('practice_choose_card_answer:'))
async def practice_choose_card_answer(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    choice = await get_choice_spread(call.from_user.id)

    deck_configs = {
        'deviantmoon': (450, 830, 143, 140, 0, 80),
        'manara': (450, 830, 143, 140, 0, 80),
        'aftertarot': (450, 830, 143, 140, 20, 200),
        'magicalforest': (500, 830, 105, 140, 0, 200),
        'wildwood': (500, 830, 105, 140, 0, 200),
        'vikaoracul': (530, 830, 77, 140, 0, 50),
        'vikanimaloracul': (530, 830, 77, 140, 0, 50),
        'raider': (480, 830, 124, 140, 0, 100)
    }

    w, h, x, y, col1, col2 = deck_configs.get(choice, (500, 830, 105, 140, 0, 150))

    image = Image.new('RGB', (1920, 1080), color = 'white')
    num = [call.data.split(':')[1], call.data.split(':')[2], call.data.split(':')[3]]

    card_paths = [await get_path_cards(choice, num[i]) for i in range(3)]
    images = []
    for i, path in enumerate(card_paths):
        path = Image.open(path).resize((w, h))
        images.append(path)

    image.paste(images[2], ((3 * x + 2 * w), y))
    image.paste(images[1], ((2 * x + w), y))
    image.paste(images[0], (x, y))

    draw_text = ImageDraw.Draw(image)
    draw_text.text((759, 990), 'from @ForestSpiritLi', font = FONT_L, fill = 'black')

    await bot.send_photo(call.message.chat.id, photo = await get_buffered_image(image))


@router.callback_query(IsReply(), F.data == 'practice_quiz')
@use_user_statistics
async def practice_quiz(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    await bot.delete_message(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id
    )

    numbers = sample(range(0, 74), 3)
    for num in numbers:
        card = await execute_select("select practice.name from practice where number = $1", (num,))
        correct_answer = await execute_select("select quiz_02 from practice where number = $1", (num,))

        false = sample(range(0, 74), 4)
        if num in false:
            false = sample(range(0, 74), 4)

        answers = []
        for el in false:
            false_answer = await execute_select("select quiz_02 from practice where number = $1", (el,))
            answers.append(false_answer)
        answers.append(correct_answer)
        random.shuffle(answers)

        c = await check_correct_answer(answers, correct_answer)

        await bot.send_poll(
            call.message.chat.id,
            f'Какое значение может быть у карты {card}?',
            [f'{ans}' for ans in answers],
            type = 'quiz',
            correct_option_id = c,
            is_anonymous = False
        )


async def check_correct_answer(answers, correct_answer):
    for x, el in enumerate(answers):
        if el == correct_answer:
            return x
    return 0
