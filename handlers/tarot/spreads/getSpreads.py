from aiogram.utils.keyboard import InlineKeyboardBuilder

from functions.createThreeCardsImage import send_image_three_cards, get_image_three_cards
from main import bot
from PIL import ImageDraw
import textwrap
from aiogram import types, Router, F
from functions.createImage import text_size
from constants import FONT_L
import re
from functions.statistics import delete_message
from .spreadsConfig import SPREADS

spread_buttons = []
builder = InlineKeyboardBuilder()
for spread_key in SPREADS.keys():
    spread_button_text = next(iter(SPREADS[spread_key]['name']))

    builder.button(text = spread_button_text.capitalize().replace('_', ' '),
                   callback_data = spread_key)

builder.adjust(2)
spreads_keyboard = builder.as_markup()

router = Router()


async def draw_spread(image, spread_name):
    draw_text = ImageDraw.Draw(image)
    current_h, pad = 80, 715
    count = 0
    for text, font in SPREADS[spread_name]['image']:
        count += 1
        para = textwrap.wrap(text, width = 30)
        for line in para:
            w, h = draw_text.textbbox((0, 0), line, font = font)
            draw_text.text(((pad - w) / 2, current_h), line, font = font)
        pad += 1200
        if count == 2:
            pad += 20
    return image


@router.message(F.text.lower().startswith("триплет"))
async def get_image_triplet(message: types.Message):
    image, num = await get_image_three_cards(message.from_user.id)
    text = message.text.split(" ")[1:]
    text = ' '.join(text)
    draw_text = ImageDraw.Draw(image)
    if len(text) == 0:
        draw_text.text((870, 80), 'Триплет', fill = 'white', font = FONT_L)
    else:
        if re.search(r".+-.+-.+", text):
            msg = message.text.split(" ")[1:]
            msg = " ".join(msg)
            test = msg.split("-")

            count = 0
            current_h, pad = 80, 695
            for text in test:
                count += 1
                para = textwrap.wrap(text, width = 30)
                for line in para:
                    w, h = text_size(line, FONT_L)
                    draw_text.text(((pad - w) / 2, current_h), line, font = FONT_L)
                pad += 1210
        else:
            current_h, pad = 80, 1910
            para = textwrap.wrap(str(text), width = 100)
            for line in para:
                w, h = text_size(line, FONT_L)
                draw_text.text(((pad - w) / 2, current_h), line, font = FONT_L)

    await send_image_three_cards(message, message.from_user.first_name, image, num)


@router.message(F.text.lower().startswith("расклад"))
async def get_spread(message: types.Message):
    if re.search(r'\bрасклад\Z', message.text.lower()):
        msg = await bot.send_message(
            text = f"<b>Какой расклад вы хотите получить?</b> \n<code>Сосредоточьтесь на своей ситуации и нажмите на кнопку ниже. </code>",
            chat_id = message.chat.id,
            reply_markup = spreads_keyboard,
            reply_to_message_id = message.message_id)
        await delete_message(msg, 30)
    elif re.search(r'^расклад\b', message.text.lower()):
        spread_name = None
        for spread in SPREADS:
            if SPREADS[spread]['keywords'] & set(message.text.lower().split()):
                spread_name = spread
                break
        if spread_name:
            if spread_name in list(SPREADS.keys())[-4:]:
                spread_func = SPREADS[spread_name]['func']
                await spread_func(message, spread_name)
            else:
                image, num = await get_image_three_cards(message.from_user.id)
                image = await draw_spread(image, spread_name)
                await send_image_three_cards(message, message.from_user.first_name, image, num, spread_name)
    else:
        pass


@router.callback_query(lambda call: call.data in SPREADS.keys())
async def spreads_callback(call: types.CallbackQuery):
    await call.answer()
    try:
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            spread_name = call.data
            if spread_name in list(SPREADS.keys())[-4:]:
                spread_func = SPREADS[spread_name]['func_cb']
                await spread_func(call)
            else:
                image, num = await get_image_three_cards(call.from_user.id)
                image = await draw_spread(image, spread_name)
                await send_image_three_cards(call.message, call.from_user.first_name, image, num, spread_name)
    except:
        pass
