import pendulum
from typing import Tuple, Any
from database import execute_select
from main import bot
import asyncio
from functions.createImage import get_choice_spread, get_random_num
import keyboard as kb
from aiogram import Router, F, types
import constants as config
from .getCardsImage import set_card_image, set_days_card_image

router = Router()


async def get_one_card(message: types.Message, user_id: int, *keyboard: Any) -> Tuple[str, int]:
    choice = await get_choice_spread(user_id)

    num = await get_random_num(choice, 1)
    sticker_id = execute_select("select {} from stickers where number={};".format(choice, num))

    reply_to_message_id: int = message.message_id

    if keyboard:
        msg = await bot.send_sticker(message.chat.id, sticker = sticker_id, reply_markup = kb.dop_card_keyboard,
                                     reply_to_message_id = reply_to_message_id)
        await asyncio.sleep(60)
        await bot.edit_message_reply_markup(chat_id = message.chat.id, message_id = msg.message_id,
                                            reply_markup = None)
    else:
        await bot.send_sticker(message.chat.id, sticker = sticker_id, reply_to_message_id = reply_to_message_id)

    return choice, num


@router.message(F.text.lower().startswith("карта"))
async def get_card(message: types.Message):
    card_found = False

    keywords_card_days = {
        tuple(config.AWARE_TODAY_SPREAD): ('day_aware', pendulum.today('Europe/Kiev')),
        tuple(config.AWARE_TOMORROW_SPREAD): ('day_aware', pendulum.tomorrow('Europe/Kiev')),
        tuple(config.CONCLUSION_TODAY_SPREAD): ('day_conclusion', pendulum.today('Europe/Kiev')),
        tuple(config.CONCLUSION_TOMORROW_SPREAD): ('day_conclusion', pendulum.tomorrow('Europe/Kiev')),
        tuple(config.ADVICE_TODAY_SPREAD): ('day_advice', pendulum.today('Europe/Kiev')),
        tuple(config.ADVICE_TOMORROW_SPREAD): ('day_advice', pendulum.tomorrow('Europe/Kiev')),
        tuple(config.TOMORROW_SPREAD): ('day_card', pendulum.tomorrow('Europe/Kiev')),
        tuple(config.TODAY_SPREAD): ('day_card', pendulum.today('Europe/Kiev'))
    }

    keywords_cards = {
        tuple(config.ADVICE_SPREAD): ('advice'),
        tuple(config.YESNO_SPREAD): ('yesno')
    }

    for keywords_tuple, (image_type, date) in keywords_card_days.items():
        if any(word in message.text.lower() for word in keywords_tuple):
            await set_days_card_image(message, image_type, date.format('DD.MM'))
            card_found = True
            break

    if not card_found:
        for keywords_tuple, (image_type) in keywords_cards.items():
            if any(word in message.text.lower() for word in keywords_tuple):
                await set_card_image(message, image_type)
                card_found = True
                break

    if not card_found:
        await get_one_card(message, message.from_user.id, True)


@router.message(F.text.lower() == "доп")
async def one_dop_card_text(message: types.Message):
    await get_one_card(message, message.from_user.id)


@router.message(F.data.startswith('dop_card_'))
async def dop_card(call: types.CallbackQuery):
    try:
        await call.answer()
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            num_cards = int(call.data.split('_')[-1])
            await call.message.answer(f"<tg-spoiler><b>ㅤㅤㅤㅤㅤДопыㅤㅤㅤㅤ</b></tg-spoiler>")
            for i in range(num_cards):
                await get_one_card(call.message, call.from_user.id)
    except Exception:
        pass
