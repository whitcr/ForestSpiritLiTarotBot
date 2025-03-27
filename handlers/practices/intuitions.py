from aiogram import Router, types, Bot, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from random import randint

from database import execute_select
import keyboard as kb
from filters.baseFilters import IsReply
from functions.messages.messages import typing_animation_decorator
from middlewares.statsUser import use_user_statistics

router = Router()


@router.callback_query(IsReply(), lambda callback: callback.data == 'practice_menu_intuition')
@use_user_statistics
async def practice_menu_intuition(call: types.CallbackQuery, bot: Bot):
    await bot.edit_message_text(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        text = (
            "<b>Карта</b> — вы должны будете почувствовать скрытую карту.\n\n"
            "<b>Выбор карты</b> — вам надо будете почувствовать определенную карту.\n\n"
            "<b>Заливка</b> — надо будет почувствовать, что скрывается за заливкой."
        ),
        reply_markup = kb.practice_menu_intuition_keyboard
    )


@router.callback_query(IsReply(), F.data == 'practice_zalivka')
@typing_animation_decorator(initial_message = "Создаю")
@use_user_statistics
async def practice_zalivka(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    await bot.delete_message(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id
    )

    max_number = await execute_select("SELECT number FROM zalivka ORDER BY number DESC LIMIT 1")
    num = randint(5, max_number)

    photo_zalivka = await execute_select("SELECT zalivka FROM zalivka WHERE number = $1", (num,))

    builder = InlineKeyboardBuilder()
    builder.button(
        text = "Показать ответ",
        callback_data = f"practice_zalivka_answer:{num}"
    )

    await bot.send_photo(
        call.message.chat.id,
        photo = photo_zalivka,
        caption = "Сосредоточьтесь и почувстуйте, что именно находится за заливкой."
                  "\n<code>При вызове нового задания ответ прошлого будет утерян, "
                  "\nответ может узнать только тот, кто взял задание.</code>",
        reply_markup = builder.as_markup()
    )


@router.callback_query(IsReply(), F.data.startswith('practice_zalivka_answer:'))
async def practice_zalivka_answer(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    num = int(call.data.split(':')[1])

    photo_original = await execute_select(
        "SELECT zalivka_original FROM zalivka WHERE number = $1",
        (num,)
    )
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text = 'Меню', callback_data = f'practice_menu_tarot')
    keyboard.button(text = 'Еще заливку!', callback_data = f'practice_zalivka')
    await bot.send_photo(call.message.chat.id, photo = photo_original,
                         reply_markup = keyboard.as_markup(),
                         reply_to_message_id = call.message.reply_to_message.message_id)
