from aiogram import types, Router, F
from aiogram.filters import or_f

from database import execute_select, execute_select_all, execute_query
from filters.baseFilters import IsReply
from filters.subscriptions import SubscriptionLevel
from functions.messages.messages import typing_animation_decorator, send_long_message
from functions.gpt.requests import get_cards_day_meanings
from middlewares.statsUser import UserStatisticsMiddleware

router = Router()
router.message.middleware(UserStatisticsMiddleware())
router.callback_query.middleware(UserStatisticsMiddleware())


@router.callback_query(IsReply(), F.data.startswith("get_day_spread_meaning"), SubscriptionLevel(1, True),
                       flags = {"use_user_statistics": True})
@typing_animation_decorator(initial_message = "Трактую")
async def process_callback_day_spread_meaning(call: types.CallbackQuery):
    await call.answer()
    date = call.data.split('_')[-1]

    meaning = await execute_select(f"SELECT meaning FROM spreads_day WHERE date = $1 AND user_id = $2",
                                   (date, call.from_user.id,))

    if meaning:
        await send_long_message(call.message, meaning)
        return
    else:

        nums = await execute_select_all(
            "SELECT day_card, day_card_dop_1, day_card_dop, day_conclusion, day_advice, day_aware "
            "FROM spreads_day WHERE date = $1 AND user_id = $2",
            (date, call.from_user.id)
        )

        cards = []
        for i in nums[0]:
            name = await execute_select("SELECT name FROM cards WHERE number = $1", (i,))
            cards.append(name)

        day_card = cards[0]
        day_card_dop_1 = cards[1]
        day_card_dop = cards[2]
        day_conclusion = cards[3]
        day_advice = cards[4]
        day_aware = cards[5]

        text = (f"Карта дня: {day_card}, дополнительные карты - {day_card_dop_1}, {day_card_dop}\n"
                f"Угроза дня: {day_aware}\n"
                f"Совет дня: {day_advice}\n"
                f"Итог дня: {day_conclusion}")

        message = await get_cards_day_meanings(text)

        await execute_query("UPDATE spreads_day SET meaning = $1 WHERE date = $2 AND user_id = $3",
                            (message, date, call.from_user.id))

        await call.message.answer(message)


@router.callback_query(IsReply(), F.data.startswith("get_time_spread_meaning_"), SubscriptionLevel(1),
                       flags = {"use_user_statistics": True})
@typing_animation_decorator(initial_message = "Трактую")
async def process_callback_day_spread_meaning(call: types.CallbackQuery):
    await call.answer()
    theme = call.data.split('_')[-1]
    table = f"spreads_{theme}"

    meaning = await execute_select(f"SELECT meaning FROM {table} WHERE user_id = $1", (call.from_user.id,))

    if meaning:
        await send_long_message(call.message, meaning)
        return
    else:
        nums = await execute_select_all(
            f"SELECT p1, p2, p3, n1, n2, n3, advice, threat "
            f"FROM {table} WHERE  user_id = $1",
            (call.from_user.id,)
        )

        cards = []
        for i in nums[0]:
            name = await execute_select("SELECT name FROM cards WHERE number = $1", (i,))
            cards.append(name)

        if theme == 'week':
            theme = "недели"
        elif theme == 'month':
            theme = "месяца"

        text = (f"Позитивные события {theme}: {cards[0]},{cards[1]}, {cards[2]}\n"
                f"Негативные события {theme}: {cards[3]},{cards[4]}, {cards[5]}\n"
                f"Угроза {theme}: {cards[6]}\n"
                f"Совет {theme}: {cards[7]}\n")

        message = await get_cards_day_meanings(text)

        await execute_query(f"UPDATE {table} SET meaning = $1 WHERE user_id = $2",
                            (message, call.from_user.id))

        await call.message.answer(message)
