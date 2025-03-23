import asyncio
import pytz
from datetime import datetime
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from constants import CARDS
from database import execute_query, execute_select, execute_select_all

router = Router()
MARATHONER_CHAT = -1001445412679


# закинуть в основное расписание
# asyncio.create_task(schedule_notifications(bot))

async def check_and_create_db():
    await execute_query(
        """CREATE TABLE IF NOT EXISTS maraphone_records (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        arcane TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        ()
    )
    await execute_query(
        """CREATE TABLE IF NOT EXISTS maraphone_arcanes (
        id SERIAL PRIMARY KEY,
        number FLOAT NOT NULL,
        arcane TEXT NOT NULL,
        text TEXT NOT NULL)""",
        ()
    )


class Records(StatesGroup):
    arcane = State()
    day = State()


async def get_today_arcane():
    arcane = await execute_select(
        "SELECT arcane, text FROM maraphone_arcanes WHERE number = 99"
    )
    if arcane:
        return arcane[0], arcane[1]
    return "Не найден", "Нет информации."


async def morning_arcane_notification(bot: Bot):
    arcane, description = await get_today_arcane()
    text = f"🌞 Доброе утро! Сегодня мы проживаем аркан <b>{arcane}</b>\n\n{description}"
    await bot.send_message(MARATHONER_CHAT, text = text, parse_mode = "HTML")


async def evening_record_notification(bot: Bot):
    text = "🌙 Как насчет записать результаты сегодняшнего дня?"
    await bot.send_message(MARATHONER_CHAT, text = text)


# гавно переделать
async def schedule_notifications(bot: Bot):
    tz = pytz.timezone("Europe/Kiev")

    while True:
        now = datetime.now(tz)
        morning_time = now.replace(hour = 9, minute = 0, second = 0, microsecond = 0)
        evening_time = now.replace(hour = 21, minute = 0, second = 0, microsecond = 0)

        if now < morning_time:
            sleep_time = (morning_time - now).total_seconds()
            await asyncio.sleep(sleep_time)
            await morning_arcane_notification(bot)

        elif now < evening_time:
            sleep_time = (evening_time - now).total_seconds()
            await asyncio.sleep(sleep_time)
            await evening_record_notification(bot)

        else:
            await asyncio.sleep(3600)


@router.message(F.text.lower() == "марафон")
async def marathon_info(message: Message, bot: Bot):
    await check_and_create_db()

    arcane, arcane_text = await get_today_arcane()
    date = datetime.now(pytz.timezone("Europe/Kiev")).strftime("%d.%m")

    text = (
        f"📅 <b>Марафон</b>\n"
        f"Сегодня <b>{date}</b>\n\n"
        f"🌟 Сегодняшний Аркан: <b>{arcane}</b>\n\n"
        f"{arcane_text}"
    )

    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text = "📖 Мой дневник")
    keyboard.button(text = "✍ Записать результат")
    keyboard.adjust(1)

    await bot.send_message(
        message.chat.id, text = text, reply_markup = keyboard.as_markup(resize_keyboard = True), parse_mode = "HTML"
    )


@router.callback_query(F.data == "rec_maraphone")
async def rec_maraphone(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Какой аркан вы сегодня проживали?")
    await state.set_state(Records.arcane)


@router.message(Records.arcane)
async def get_day_maraphone(message: Message, state: FSMContext):
    await state.update_data(arcane = message.text)
    arcane = message.text.lower()

    if any(word in arcane for word in CARDS):
        await message.answer("Опишите то, как проигрался ваш сегодняшний аркан.")
        await state.set_state(Records.day)
    else:
        await message.answer("Это какая-то новая колода? Напиши по Уэйту.")
        await state.set_state(Records.arcane)


@router.message(Records.day)
async def get_rec_maraphone(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = message.from_user.id
        arcane = data["arcane"]
        text = message.text

        existing_record = await execute_select(
            "SELECT text FROM maraphone_records WHERE user_id = %s AND arcane = %s",
            (user_id, arcane),
        )

        if existing_record:
            text = f"{existing_record[0]}\n\n{text}"
        else:
            await execute_query(
                "INSERT INTO maraphone_records (user_id, arcane, text) VALUES (%s, %s, %s)",
                (user_id, arcane, text),
            )

        await execute_query(
            "UPDATE maraphone_records SET text = %s WHERE user_id = %s AND arcane = %s",
            (text, user_id, arcane),
        )

        await message.answer("Записано!")
    except Exception as e:
        print(e)
        await message.answer("Что-то пошло не так.")
    finally:
        await state.clear()


@router.message(F.text.lower() == "мой дневник")
async def show_rec_maraphone(message: Message):
    if message.chat.id == MARATHONER_CHAT:
        try:
            user_id = message.from_user.id
            records = await execute_select_all(
                "SELECT arcane, text FROM maraphone_records WHERE user_id = %s",
                (user_id,),
            )

            if not records:
                await message.answer("Ваш дневник пуст.")
                return

            info = [f"<b>{arcane}</b>\n\n{text}" for arcane, text in records]

            full_text = "\n\n".join(info)
            if len(full_text) > 4096:
                for part in [full_text[i:i + 4096] for i in range(0, len(full_text), 4096)]:
                    await message.answer(f"<b>ДНЕВНИК ПО ПРОЖИВАНИЮ АРКАНОВ</b>\n\n{part}", parse_mode = "HTML")
            else:
                await message.answer(f"<b>ДНЕВНИК ПО ПРОЖИВАНИЮ АРКАНОВ</b>\n\n{full_text}", parse_mode = "HTML")
        except Exception as e:
            print(e)
            await message.answer("Ошибка при получении данных.")
