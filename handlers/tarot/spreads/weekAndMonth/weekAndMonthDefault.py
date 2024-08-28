from aiogram.types import CallbackQuery
from database import execute_query, execute_select
from filters.baseFilters import IsReply
from functions.cards.createSixCards import send_image_six_cards, create_image_six_cards
from functions.messages.messages import get_reply_message, typing_animation_decorator
from handlers.tarot.spreads.weekAndMonth.weekAndMonthPremium import get_week_spread_premium
from PIL import ImageDraw

from aiogram import types, Router, F, Bot
from functions.cards.create import get_choice_spread

from constants import FONT_M
from constants import DECK_MAP
from keyboard import create_week_spread_keyboard, create_month_spread_keyboard

router = Router()


async def get_month_week_spread(bot, message, spread_name):
    user_id = message.from_user.id
    spread_name = spread_name.split('_')[0]

    is_booster = await execute_select("SELECT boosted FROM users WHERE user_id = $1", (user_id,))
    subscription = await execute_select("SELECT subscription FROM users WHERE user_id = $1", (user_id,))

    if is_booster >= 1 or subscription == 'premium' or 'premiumPlus':
        if spread_name == "week" and is_booster >= 1:
            if message.chat.type == 'private':
                result = await execute_select("SELECT boosted FROM spreads_week WHERE user_id = $1", (user_id,))

                if result == 0:
                    await execute_query("INSERT INTO spreads_week (user_id, boosted) VALUES ($1, $2)", (user_id, True))
                    await get_week_spread_premium(bot, user_id)
                else:
                    await bot.send_message(message.chat.id,
                                           text = "На этой неделе ты уже сделал свой премиум "
                                                  "расклад на неделю, жди следующей.")
            else:
                await bot.send_message(message.chat.id,
                                       text = "Так как твой расклад премиальный, используй команду у меня в ЛС",
                                       reply_to_message_id = await get_reply_message(message))
            return

    table = f"spreads_{spread_name}"
    file_id = await execute_select(f"SELECT file_id FROM {table} WHERE user_id = '{user_id}'")

    if file_id:
        await bot.send_photo(message.chat.id, photo = file_id, reply_to_message_id = message.message_id)

    else:
        choice = await get_choice_spread(message.from_user.id)
        deck_type = DECK_MAP[choice]
        keyboard = create_month_spread_keyboard if spread_name == "month" else create_week_spread_keyboard
        theme = "месяц" if spread_name == "month" else "неделю"
        await bot.send_message(message.chat.id,
                               text = f"<code>Ты уверен в выборе своей колоды?\nТвоя колода — {deck_type}\n"
                                      f"Расклад на {theme} делается лишь единожды.</code>",
                               reply_markup = keyboard, reply_to_message_id = await get_reply_message(message))


async def get_month_week_spread_cb(bot, call: types.CallbackQuery):
    spread_name = call.data.split("_")[0]
    await get_month_week_spread(bot, call.message, f"{spread_name}_callback")


@typing_animation_decorator(initial_message = "Раскладываю")
async def create_spread_image(bot, call: CallbackQuery, spread_type: str):
    await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)
    image, cards = await create_image_six_cards(call.from_user.id, spread_type)
    draw_text = ImageDraw.Draw(image)

    draw_text.text((115, 245), f'Совет {spread_type}', font = FONT_M, fill = 'white')
    draw_text.text((810, 10), 'Позитивные события', font = FONT_M, fill = 'white')
    draw_text.text((1574, 245), f'Угроза {spread_type}', font = FONT_M, fill = 'white')
    draw_text.text((820, 514), f'Расклад {spread_type}', font = FONT_M, fill = 'white')
    draw_text.text((805, 1010), 'Негативные события', font = FONT_M, fill = 'white')
    draw_text.text((1295, 1025), 'from ForestSpiritLi', font = FONT_M, fill = 'white')

    await send_image_six_cards(bot, call.message, call.from_user.first_name, image, spread_type)


@router.callback_query(IsReply(), F.data == 'create_month_spread')
async def get_month_spread_image(call: CallbackQuery, bot: Bot):
    await create_spread_image(bot, call, 'месяца')


@router.callback_query(IsReply(), F.data == 'create_week_spread')
async def get_week_spread_image(call: CallbackQuery, bot: Bot):
    await create_spread_image(bot, call, 'недели')
