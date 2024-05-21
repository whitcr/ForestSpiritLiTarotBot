import pytz
from database import execute_select, execute_query
from main import bot
from PIL import Image, ImageDraw
from PIL import ImageFilter
from io import BytesIO
from datetime import datetime
import asyncio
import textwrap
import numpy as np
from aiogram import types, Router
from functions.createImage import get_path_background, get_gradient_3d,\
    get_path_cards_sync, get_random_num_sync, text_size
from constants import FONT_L, FONT_S, FONT_XL
import keyboard as kb
from typing import Union
from constants import DECK_MAP
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from functions.statistics import delete_message

router = Router()


async def generate_ex_decks_keyboard(triplet_type: Union["mtriplet", "striplet"]):
    buttons = []
    for key, value in DECK_MAP.items():
        button = InlineKeyboardButton(text = value, callback_data = f"{triplet_type}_" + key + "_experimental")
        buttons.append(button)

    button = InlineKeyboardButton(text = "Очистить колоды", callback_data = f"{triplet_type}_clear_experimental")
    buttons.append(button)
    choose_ex_cards_keyboard = InlineKeyboardMarkup(resize_keyboard = True, row_width = 3).add(*buttons)
    return choose_ex_cards_keyboard


def generate_cards(choices, triplet_type: Union["mtriplet", "striplet"]):
    cards = []
    for choice in choices:
        if triplet_type == "striplet":
            num = get_random_num_sync(choice, 3)
        else:
            num = get_random_num_sync(choice, 6)
        cards.extend([get_path_cards_sync(choice, num[i]) for i in range(3)])
    return cards[::-1]


async def get_choices(user_id, triplet_type: Union["mtriplet", "striplet"]):
    try:
        result = execute_select(f"SELECT {triplet_type} FROM users WHERE user_id = %s", (user_id,))
        return result.split(', ')
    except Exception as e:
        default_choices = ["raider", "manara", "deviantmoon"]

        if triplet_type == "mtriplet":
            default_choices.extend(["ceccoli", "decameron", "vikanimaloracul"])
        return default_choices


async def send_triplet_image(image, text, date, message, triplet_type: Union["mtriplet", "striplet"]):
    draw_text = ImageDraw.Draw(image)
    if len(text) == 0:
        if triplet_type == "mtriplet":
            draw_text.text((1450, 70), 'МТриплет', font = FONT_XL, fill = 'white')
        else:
            draw_text.text((1450, 70), 'СуперТриплет', font = FONT_XL, fill = 'white')
    else:
        current_h, pad = 70, 1910
        para = textwrap.wrap(str(text), width = 100)
        for line in para:
            w, h = text_size(line, FONT_XL)
            draw_text.text(((3200 - w) / 2, current_h), line, font = FONT_XL)
            current_h += h + pad
    draw_text = ImageDraw.Draw(image)
    draw_text.text((1350, 1900), 'from @ForestSpiritLi', fill = 'white', font = FONT_XL)
    draw_text.text((1550, 10), date, fill = 'white', font = FONT_XL)
    para = textwrap.wrap(f"for {message.from_user.first_name}", width = 30)
    current_h, pad = 1950, 10
    for line in para:
        w, h = text_size(line, FONT_S)
        draw_text.text(((3100 - w) / 2, current_h), line, font = FONT_L)
        current_h += h + pad
    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'JPEG')
        bio.seek(0)
        reply_to_message_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
        await bot.send_photo(message.chat.id, photo = BufferedInputFile(bio), reply_to_message_id = reply_to_message_id)


@router.message(lambda message: message.text.lower().startswith("мтриплет"))
async def get_mtriplet(message: types.Message):
    try:

        def generate_image(cards, background_path):
            w, h = 340, 560
            x, y = 165, 140
            col1, col2 = 0, 130
            color = np.random.randint(col1, col2, size = 6)
            array = get_gradient_3d(3200, 2000, (color[0], color[1], color[2]),
                                    (color[3], color[4], color[5]),
                                    (True, False, True))
            image = Image.fromarray(np.uint8(array))

            background = Image.open(background_path)
            background = background.resize((3200, 2000))
            background = background.filter(ImageFilter.GaussianBlur(radius = 3))
            image = Image.blend(image, background, alpha = .3)

            positions = [
                (6 * x + 5 * w, y + 1200),
                (5 * x + 4 * w, y + 1200),
                (4 * x + 3 * w, y + 1200),
                (6 * x + 5 * w, y + 600),
                (4 * x + 3 * w, y + 600),
                (5 * x + 4 * w, y + 600),
                (5 * x + 4 * w, y),
                (6 * x + 5 * w, y),
                (4 * x + 3 * w, y),
                (3 * x + 2 * w, y + 1200),
                (2 * x + w, y + 1200),
                (x, y + 1200),
                (3 * x + 2 * w, y + 600),
                (2 * x + w, y + 600),
                (x, y + 600),
                (3 * x + 2 * w, y),
                (2 * x + w, y),
                (x, y)
            ]

            for i, position in enumerate(positions):
                card = Image.open(cards[i])
                card = card.resize((w, h))
                image.paste(card, position)
            return image

        date = datetime.now(pytz.timezone('Europe/Kiev')).strftime("%d.%m")
        msg = await message.reply("Ваш мегатриплет генерируется...")
        user_id = message.from_user.id

        try:
            choices = get_choices(user_id, "mtriplet")
        except Exception as e:
            print(f"Error getting choices: {e}")
            choices = ["raider", "manara", "deviantmoon", "ceccoli", "decameron", "vikanimaloracul"]

        background_path = await get_path_background()

        cards = await asyncio.to_thread(generate_cards, choices)

        image = await asyncio.to_thread(generate_image, cards, background_path)

        text = message.text.split(" ")[1:]
        text = ' '.join(text)

        await send_triplet_image(image, text, date, message, "mtriplet")
        await delete_message(msg)
    except Exception as e:
        await message.reply("— Что-то пошло не так, скорее всего у вас выбрано менее 6 колод.")


@router.message(lambda message: message.text.lower().startswith("стриплет"))
async def get_striplet(message: types.Message):
    try:

        def generate_image(cards, background_path):
            w, h = 340, 560
            x, y = 130, 140
            col1, col2 = 0, 130

            color = np.random.randint(col1, col2, size = 6)
            array = get_gradient_3d(1800, 2000, (color[0], color[1], color[2]),
                                    (color[3], color[4], color[5]),
                                    (True, False, True))
            image = Image.fromarray(np.uint8(array))

            background = Image.open(background_path)
            background = background.resize((1800, 2000))
            background = background.filter(ImageFilter.GaussianBlur(radius = 3))
            image = Image.blend(image, background, alpha = .3)

            positions = [
                (3 * x + 2 * w + 110, y + 1200),
                (2 * x + w + 110, y + 1200),
                (x + 110, y + 1200),
                (3 * x + 2 * w + 110, y + 600),
                (2 * x + w + 110, y + 600),
                (x + 110, y + 600),
                (3 * x + 2 * w + 110, y),
                (2 * x + w + 110, y),
                (x + 110, y)
            ]

            for i, position in enumerate(positions):
                card = Image.open(cards[i])
                card = card.resize((w, h))
                image.paste(card, position)

            return image

        date = datetime.now(pytz.timezone('Europe/Kiev')).strftime("%d.%m")
        msg = await message.reply("Ваш супертриплет генерируется...")
        user_id = message.from_user.id

        try:
            choices = get_choices(user_id, "striplet")
        except Exception as e:
            choices = ["raider", "manara", "deviantmoon"]

        background_path = await get_path_background()

        cards = await asyncio.to_thread(generate_cards, choices)

        image = await asyncio.to_thread(generate_image, cards, background_path)

        text = message.text.split(" ")[1:]
        text = ' '.join(text)

        await send_triplet_image(image, text, date, message, "striplet")
        await delete_message(msg)
    except Exception as e:
        await message.reply("— Что-то пошло не так, скорее всего у вас выбрано менее 3 колод.")


@router.message(lambda message: message.text.lower().startswith("настройки"))
async def set_triplets(message: types.Message):
    await message.reply("Пожалуйста, выберите, что вы хотите настроить", reply_markup = kb.set_triplet_keyboard)


@router.callback_query(lambda call: call.data in ['set_mtriplet', "set_striplet"])
async def set_triplets_choices(call: types.CallbackQuery):
    await call.answer()
    type = call.data.split("_")[1]
    keyboard = await generate_ex_decks_keyboard(type)
    choice = execute_select(f"SELECT {type} FROM users WHERE user_id = %s", (call.from_user.id,))

    new_choice = []
    try:
        for i in choice.split(', '):
            name = DECK_MAP[i]
            new_choice.append(name)
        new_choice = ", ".join(new_choice)
    except:
        new_choice = "не выбрано"

    if type == "mtriplet":
        type_name = "мегатриплета на шесть колод"
    else:
        type_name = "cупертриплета на три колоды"

    await bot.edit_message_text(chat_id = call.message.chat.id,
                                message_id = call.message.message_id,
                                text = f"Ваши выбранные колоды для {type_name}: <b> {new_choice} </b>.\n\nЕсли у вас ничего не "
                                       f"выбранно, нажимайте на кнопки ниже по очереди выбора."
                                       f" \n\n<i>Если вы хотите изменить выбор, нажмите 'Очистить колоды'</i>.",
                                reply_markup = keyboard)


@router.callback_query(lambda call: call.data.endswith('_experimental'))
async def get_ex_choices(call: types.CallbackQuery):
    await call.answer()
    type = call.data.split('_')[0]
    keyboard = await generate_ex_decks_keyboard(type)
    if call.data == f"{type}_clear_experimental":
        execute_query(f"UPDATE users SET {type} = NULL where user_id = %s", (call.from_user.id,))
        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = f"Ваши колоды были очищены. Можете выбирать еще раз.",
                                    reply_markup = keyboard)
    else:
        try:
            old_choice = execute_select(f"SELECT {type} FROM users WHERE user_id = %s", (call.from_user.id,))

            choice = old_choice + ", " + call.data.split("_")[1]
            check_choice = choice
            if type == "mtriplet" and check_choice.count(", ") > 5 or type == "striplet" and check_choice.count(
                    ", ") > 2:
                choice = old_choice
        except:
            check_choice = "0"
            choice = call.data.split("_")[1]

        new_choice = []
        for i in choice.split(', '):
            name = DECK_MAP[i]
            new_choice.append(name)
        new_choice = ", ".join(new_choice)
        if type == "mtriplet":
            type_name = "мегатриплета на шесть колод"
        else:
            type_name = "cупертриплета на три колоды"
        if type == "mtriplet" and check_choice.count(", ") > 5 or type == "striplet" and check_choice.count(", ") > 3:
            try:
                await bot.edit_message_text(chat_id = call.message.chat.id,
                                            message_id = call.message.message_id,
                                            text = f"Ваши выбранные колоды для {type_name}:<b> {new_choice}</b>."
                                                   f"\n\nВы не можете выбрать больше, чем обозначенное количество колод."
                                                   f"\n\n<i>Если вам не нравится ваш выбор, нажмите на 'Очистить колоды'</i>",
                                            reply_markup = keyboard)
            except:
                pass
        else:
            execute_query(f"UPDATE users SET {type} = %s where user_id = %s", (choice, call.from_user.id,))

            try:
                await bot.edit_message_text(chat_id = call.message.chat.id,
                                            message_id = call.message.message_id,
                                            text = f"Ваши выбранные колоды для {type_name}: <b>{new_choice}</b>.",
                                            reply_markup = keyboard)
            except:
                pass
