from database import execute_query, execute_select
from functions.createSixCardsImage import send_image_six_cards, create_image_six_cards
from functions.createThreeCardsImage import get_image_three_cards
from main import bot
from PIL import ImageDraw

from io import BytesIO

import keyboard as kb
from aiogram import types, Router, F
from functions.createImage import get_choice_spread

from constants import FONT_M
from constants import DECK_MAP

from constants import FONT_L
from gptApi.gpt import time_spread

router = Router()


async def get_month_week_spread(message, spread_name):
    user_id = message.from_user.id
    spread_name = spread_name.split('_')[0]

    # Check if the user is a boosted user
    is_boosted = execute_select("SELECT boosted FROM users WHERE user_id = '{}'".format(user_id))

    if spread_name == "week" and is_boosted:
        if message.chat.type == 'private':
            result = execute_select("SELECT boosted FROM spreads_week WHERE user_id = '{}'".format(user_id))

            if not result:
                execute_query("INSERT INTO spreads_week (user_id, boosted) VALUES ('{}', 1)".format(user_id))
                await get_week_spread_premium(user_id)
            else:
                await bot.send_message(message.chat.id,
                                       text = "На этой неделе ты уже сделал свой премиум расклад на неделю, жди следующей.")
        else:
            reply_to_message_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
            await bot.send_message(message.chat.id,
                                   text = "Так как твой расклад премиальный, используй команду у меня в ЛС",
                                   reply_to_message_id = reply_to_message_id)
        return

    try:
        table = f"spreads_{spread_name}"
        file_id_cards = execute_select(f"SELECT file_id FROM {table} WHERE user_id = '{user_id}'")

        await bot.send_photo(message.chat.id, photo = file_id_cards, reply_to_message_id = message.message_id)
    except Exception:
        choice = await get_choice_spread(message.from_user.id)
        deck_type = DECK_MAP[choice]
        keyboard = kb.create_month_spread_keyboard if spread_name == "month" else kb.create_week_spread_keyboard
        theme = "месяц" if spread_name == "month" else "неделю"
        await bot.send_message(message.chat.id,
                               text = f"<code>Ты уверен в выборе своей колоды?\nТвоя колода — {deck_type}\nРасклад на {theme} делается лишь единожды.</code>",
                               reply_markup = keyboard, reply_to_message_id = message.message_id)


async def get_month_week_spread_cb(call: types.CallbackQuery):
    spread_name = call.data.split("_")[0]
    await get_month_week_spread(call.message, f"{spread_name}_callback")


@router.callback_query(F.data == 'create_month_spread')
async def get_month_spread_image(call: types.CallbackQuery):
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)
        image, cards = await create_image_six_cards(call.from_user.id)
        draw_text = ImageDraw.Draw(image)

        draw_text.text((115, 245), 'Совет месяца', font = FONT_M, fill = 'white')
        draw_text.text((810, 10), 'Позитивные события', font = FONT_M, fill = 'white')
        draw_text.text((1574, 245), 'Угроза месяца', font = FONT_M, fill = 'white')
        draw_text.text((828, 514), 'Расклад на месяц', font = FONT_M, fill = 'white')
        draw_text.text((805, 1010), 'Негативные события', font = FONT_M, fill = 'white')
        draw_text.text((1295, 1025), 'from ForestSpiritLi', font = FONT_M, fill = 'white')

        await send_image_six_cards(call.message, call.from_user.first_name, image, "month")


@router.callback_query(F.data == 'create_week_spread')
async def get_week_spread_image(call: types.CallbackQuery):
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)
        image, cards = await create_image_six_cards(call.from_user.id)
        draw_text = ImageDraw.Draw(image)

        draw_text.text((115, 245), 'Совет недели', font = FONT_M, fill = 'white')
        draw_text.text((810, 10), 'Позитивные события', font = FONT_M, fill = 'white')
        draw_text.text((1574, 245), 'Угроза недели', font = FONT_M, fill = 'white')
        draw_text.text((820, 514), 'Расклад на неделю', font = FONT_M, fill = 'white')
        draw_text.text((805, 1010), 'Негативные события', font = FONT_M, fill = 'white')
        draw_text.text((1295, 1025), 'from ForestSpiritLi', font = FONT_M, fill = 'white')

        await send_image_six_cards(call.message, call.from_user.first_name, image, "week")


async def get_week_spread_premium(user_id):
    THEME_MAP = ["Финансы", "Личная Жизнь", "Эмоции"]

    await bot.send_message(user_id,
                           "Спасибо тебе за буст канала Дыхание Леса, вот твой расклад на эту неделю! Расклад делается только на колоде Уэйта! (если у вас поставлена другая колода, трактовки все равно будут для Уэйта)")

    image, num = await get_image_three_cards(user_id)
    draw_text = ImageDraw.Draw(image)

    draw_text.text((230, 80), f"Карта недели", fill = 'white', font = FONT_L)
    draw_text.text((820, 80), f"Угроза недели", fill = 'white', font = FONT_L)
    draw_text.text((1450, 80), f"Совет недели", fill = 'white', font = FONT_L)

    bio = BytesIO()
    bio.name = 'image.jpeg'
    with bio:
        image.save(bio, 'JPEG')
        bio.seek(0)
        await bot.send_photo(user_id, photo = bio)

    msg = await bot.send_message(user_id, "Трактую..")
    text = await time_spread(num, "неделю")
    text = f"<b>ТРАКТОВКА РАСКЛАДА</b>\n\n{text}"
    await bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text = text)

    for THEME in THEME_MAP:
        image, num = await get_image_three_cards(user_id)
        draw_text = ImageDraw.Draw(image)

        draw_text.text((820, 80), f"{THEME} недели", fill = 'white', font = FONT_L)

        bio = BytesIO()
        bio.name = 'image.jpeg'
        with bio:
            image.save(bio, 'JPEG')
            bio.seek(0)
            await bot.send_photo(user_id, photo = bio)

        msg = await bot.send_message(user_id, "Трактую..")
        text = await time_spread(num, "неделю", THEME)
        text = f"<b>ТРАКТОВКА РАСКЛАДА</b>\n\n{text}"
        await bot.edit_message_text(chat_id = msg.chat.id, message_id = msg.message_id, text = text)

    await bot.send_message(user_id,
                           "Сохрани этот расклад, так как он делается только раз в неделю!")
