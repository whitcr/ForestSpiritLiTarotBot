from aiogram import Router, F, Bot
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
import keyboard as kb
from database import execute_select
from filters.subscriptions import SubscriptionLevel
from functions.store.temporaryStore import store_data, get_data_two_nums

router = Router()


class Cards(StatesGroup):
    arcan = State()


@router.message(StateFilter(None), F.text.lower() == "узнать аркан", SubscriptionLevel(1))
async def arcan_date(message: types.Message, state: FSMContext):
    await message.reply("Введите дату рождения в формате 31.01.2001.")
    await state.set_state(Cards.arcan)


@router.message(Cards.arcan)
async def get_arcan_date(message: types.Message, state: FSMContext):
    try:
        date = message.text
        temp = date.split(".")
        d1, d2 = map(int, str(temp[0]))
        m1, m2 = map(int, str(temp[1]))
        y1, y2, y3, y4, = map(int, str(temp[2]))

        check_day = int(temp[0])
        check_month = int(temp[1])
    except ValueError:
        await message.reply("Издеваешься? Никаких арканов не будет.")
        await state.clear()
        return
    if check_month > 12 or check_day > 31:
        await message.reply("Неправильный формат, попробуй снова.")
        await state.clear()
        return

    if check_day > 22:
        arcane = check_day - 22
    else:
        arcane = check_day

    date_sum = d1 + d2 + m1 + m2 + y1 + y2 + y3 + y4
    if date_sum > 22:
        date_sum = date_sum - 22
        if date_sum > 22:
            date_sum = date_sum - 22
    if date_sum == 22:
        date_sum = 0
    if arcane == 22:
        arcane = 0

    card1 = await execute_select("select name from cards where number = {};", (date_sum,))

    card2 = await execute_select("select name from cards where number = {};", (arcane,))

    msg = await message.reply(f"Аркан Личности — <b>{card1}.</b>\n"
                              f"Аркан Судьбы — <b>{card2}.</b>", reply_markup = kb.date_acranes_keyboard)
    await store_data(msg, date_sum, arcane)

    await state.clear()


@router.callback_query(F.data == 'personal_date_arcane')
async def personal_date_arcane(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        num1, num2 = await get_data_two_nums(call.message.message_id)

        name = await execute_select(f"SELECT name FROM meaning_raider WHERE number = {num1}")
        text = await execute_select(f"SELECT arcane_personal_date FROM meaning_raider WHERE number = {num1}")

        await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                    text = f"Аркан Личности — <b> {name}</b>\n\n{text}",
                                    reply_markup = kb.date_personal_arcane_keyboard)


@router.callback_query(F.data == 'personal_fate_arcane')
async def personal_fate_arcane(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    if call.from_user.id == call.message.reply_to_message.from_user.id:
        num1, num2 = await get_data_two_nums(call.message.message_id)

        name = await execute_select(f"SELECT name FROM meaning_raider WHERE number = {num1}")
        text = await execute_select(f"SELECT arcane_fate_date FROM meaning_raider WHERE number = {num1}")

        await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                    text = f"Аркан Судьбы — <b> {name}</b>\n\n{text}",
                                    reply_markup = kb.date_fate_arcane_keyboard)
