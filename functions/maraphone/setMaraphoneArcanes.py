from aiogram import executor, types
from bot import dp, db, bot, cursor
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import math
from random import randint
import numpy as np
import textwrap
from datetime import datetime
import pytz
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import IDFilter
from aiogram.types import ContentType, Message
import random
import keyboard as kb
import asyncio
from datetime import datetime, timedelta
import filters as ft

# @dp.message_handler(lambda message: message.text.lower() == "тест")
async def maraphone_message():
    newdate = datetime.now(pytz.timezone('Europe/Kiev'))
    date = newdate.strftime("%d.%m")

    cursor.execute("SELECT arcane from maraphone_arcanes where number = 99;")
    number = cursor.fetchone()[0]

    cursor.execute("SELECT text from maraphone_arcanes where number = 99;")
    med = cursor.fetchone()[0]
    try:
        cursor.execute("SELECT arcane from maraphone_arcanes where number = {};".format(number))
        arcane = cursor.fetchone()[0]
        cursor.execute("SELECT raider from path_decks where number = {};".format(number))
        photo = cursor.fetchone()[0]
    except:
        pass
    number = float(number) +0.5
    if number == 22:
        number = 0;
    try:
        cursor.execute("UPDATE maraphone_arcanes SET arcane = '{}' where number = 99;".format(number))
        db.commit()
        text = f"Сегодня мы проживаем аркан <b>{arcane} </b>\n\n" \
               f"{med}"

        msg = await bot.send_photo(-1001445412679, photo=open(photo, 'rb'), caption=text)
        await bot.pin_chat_message(msg.chat.id, msg.message_id)
    except:
        pass
    # await bot.pin_chat_message(-1001445412679, message_id=msg)


@dp.message_handler(lambda message: message.text.lower() == "марафон")
async def get_notif_maraphone(message: types.Message):
    if message.chat.id == -1001445412679:
        text = f"Как насчет записать результаты сегодняшнего дня?"
        await bot.send_message(-1001445412679, text=text, reply_markup=kb.rec_keyboard_maraphone)
    else:
        pass

async def notif_maraphone():
    text = f"Как насчет записать результаты сегодняшнего дня?"
    await bot.send_message(-1001445412679, text=text, reply_markup=kb.rec_keyboard_maraphone)

async def notif_meditate():
    text = f"Не забывайте, что вы можете перед сном помедитировать на сегодняшний Аркан, чтобы вам приснился сон с интересным сюжетом!"
    await bot.send_message(-1001445412679, text=text)

class Records(StatesGroup):
    arcane = State()
    day = State()

@dp.callback_query_handler(lambda call: call.data == 'rec_maraphone')
async def rec_marapone(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Какой аркан вы сегодня проживали?")
    await Records.arcane.set()

@dp.message_handler(state=Records.arcane)
async def get_day_maraphone(message: types.Message, state: FSMContext):
        await state.update_data(arcane=message.text)
        data = await state.get_data()
        arcane = str(data['arcane'])
        if any(word in arcane.lower() for word in ft.CARDS):
            await message.answer(
                "Опишите то, как проигрался ваш сегодняшний аркан. Любые подробности, любые мелочи будут уместны.")
            await Records.day.set()
        else:
            await message.answer(
                "Это какая-то новая колода? Не слышал про такой Аркан, напиши по Уэйту.")
            await Records.arcane.set()

@dp.message_handler(state=Records.day)
async def get_rec_maraphone(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        await state.update_data(text=message.text)
        data = await state.get_data()
        arcane = str(data['arcane'])
        text = str(data['text'])
        try:
            cursor.execute("SELECT text from maraphone_records where user_id = '{}' and arcane = '{}' ;".format(user_id, arcane))
            old_text = cursor.fetchone()[0]
            text = f"{old_text}\n\n{text}"
        except:
            text = text
            cursor.execute("insert into maraphone_records (user_id, arcane) values ({}, '{}')".format(user_id, arcane))
        cursor.execute("UPDATE maraphone_records SET text = '{}' where user_id = {} and arcane = '{}';".format(text, user_id, arcane))
        db.commit()
        await message.answer("Записано!")
    except:
        await message.answer("Что-то пошло не так.")
    await state.finish()

@dp.message_handler(lambda message: message.text.lower() == "мой дневник")
async def show_rec_maraphone(message: types.Message, state: FSMContext):
    if message.chat.id == -1001445412679:
        try:
            user_id = message.from_user.id
            info= []
            cursor.execute("SELECT arcane from maraphone_records where user_id = '{}';".format(user_id))
            arcanes = cursor.fetchall()

            index = len(arcanes)

            cursor.execute("SELECT text from maraphone_records where user_id = '{}';".format(user_id))
            texts = cursor.fetchall()

            i=0
            while i<index:
                text = f"<b>{''.join(arcanes[i])}</b>\n\n{''.join(texts[i])}\n\n"
                i +=1
                info.append(text)

            if len(text) > 4096:
                temp = len(text)/2
                await message.answer(f"<b>ДНЕВНИК ПО ПРОЖИВАНИЮ АРКАНОВ</b>\n\n{''.join(text[:temp])}")
                await message.answer(f"{''.join(text[temp:])}")
            else:
                await message.answer(f"<b>ДНЕВНИК ПО ПРОЖИВАНИЮ АРКАНОВ</b>\n\n{''.join(info)}")
        except:
            pass
    else:
        pass