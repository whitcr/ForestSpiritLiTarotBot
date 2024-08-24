from aiogram import Router
from database import execute_select, execute_select_all, execute_query
from functions.cards.create import get_choice_spread, get_buffered_image
from handlers.tarot.spreads.day.daySpread import create_day_spread_image, create_day_keyboard
import pendulum
import asyncio

router = Router()


async def day_card_follow_schedule(bot):
    date = pendulum.today('Europe/Kiev').format('DD.MM')
    ids = await execute_select_all("select user_id from users where day_card_follow=1;")
    for user_id_tuple in ids:
        user_id = user_id_tuple[0]
        try:
            file_id = await execute_select("SELECT file_id FROM spreads_day WHERE user_id = $1 AND date = $2",
                                           (user_id, date))
            choice = await execute_select("select deck_type from spreads_day where user_id = $1 and date = $2",
                                          (user_id, date))
            if choice == 'raider':
                keyboard = await create_day_keyboard(date)
                msg = await bot.send_photo(user_id, photo = file_id, reply_markup = keyboard)
                await asyncio.sleep(200)
                try:
                    await bot.edit_message_reply_markup(chat_id = msg.chat.id, message_id = msg.message_id,
                                                        reply_markup = None)
                except:
                    pass
            else:
                await bot.send_photo(user_id, photo = file_id)
        except:
            try:
                username = await execute_select("select username from users where user_id=$1;", (user_id,))
            except:
                username = user_id
            choice = await get_choice_spread(user_id)
            image, cards, affirmation_num = await create_day_spread_image(user_id, username, date)
            msg = await bot.send_photo(user_id, photo = await get_buffered_image(image))
            file_id = msg.photo[-1].file_id
            await execute_query(
                "INSERT INTO spreads_day (date, user_id, day_card, day_card_dop_1, day_card_dop, day_conclusion, day_advice, day_aware, affirmation_of_day, file_id, deck_type) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                (date, user_id, cards[0], cards[1], cards[2], cards[3], cards[4], cards[5], affirmation_num, file_id,
                 choice)
            )
