from aiogram import Router
from database import execute_select, execute_select_all, execute_query
from filters.subscriptions import get_subscription
from functions.cards.create import text_size, get_buffered_image
from handlers.tarot.spreads.weekAndMonth.weekAndMonthDefault import create_image_six_cards
from constants import FONT_S, FONT_M
import asyncio
from PIL import ImageDraw
import textwrap

from handlers.tarot.spreads.weekAndMonth.weekAndMonthPremium import get_week_spread_premium

router = Router()


async def month_card_follow_schedule(bot):
    ids = await execute_select_all("select user_id from users where month_card_follow=1;")
    for user_id_tuple in ids:
        user_id = user_id_tuple[0]
        try:
            username = await execute_select("select username from users where user_id=$1;", (user_id,))
            subscription = await get_subscription(user_id, '2')
            is_booster = await execute_select("SELECT boosted FROM users WHERE user_id = $1", (user_id,))

            if is_booster or subscription:
                await get_week_spread_premium(user_id, bot, "месяца")
            else:
                image, cards = await create_image_six_cards(user_id)
                draw_text = ImageDraw.Draw(image)
                draw_text.text((115, 245), 'Совет месяца', font = FONT_M, fill = 'white')
                draw_text.text((810, 10), 'Позитивные события', font = FONT_M, fill = 'white')
                draw_text.text((1574, 245), 'Угроза месяца', font = FONT_M, fill = 'white')
                draw_text.text((828, 514), 'Расклад на месяц', font = FONT_M, fill = 'white')
                draw_text.text((805, 1010), 'Негативные события', font = FONT_M, fill = 'white')
                draw_text.text((1295, 1025), 'from ForestSpiritLi', font = FONT_M, fill = 'white')
                para = textwrap.wrap(f"for {username}", width = 30)
                current_h = 1050
                for line in para:
                    w, h = text_size(line, FONT_S)
                    draw_text.text(((1910 - w) / 2, current_h), line, font = FONT_S)
                    current_h += h + 110
                msg = await bot.send_photo(user_id, photo = await get_buffered_image(image))
                file_id = msg.photo[-1].file_id
                await execute_query("insert into spreads_month (user_id, file_id) values ($1, $2)", (user_id, file_id))
            await asyncio.sleep(5)
        except Exception as e:
            pass
