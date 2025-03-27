from aiogram import types, Router, F, Bot
from database import execute_select
from random import randint
import keyboard as kb
from filters.baseFilters import IsReply
from middlewares.statsUser import use_user_statistics

router = Router()


@router.callback_query(IsReply(), F.data == 'practice_menu_intuition')
@use_user_statistics
async def practice_menu_intuition(call: types.CallbackQuery, bot: Bot):
    await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                text = f"<b>Карта</b> — вы должны будете почувствовать скрытую карту.\n\n"
                                       f"<b>Выбор карты</b> — вам надо будет почувствовать определенную карту.\n\n"
                                       f"<b>Заливка</b> — надо будет почувствовать, что скрывается за заливкой.",
                                reply_markup = kb.practice_menu_intuition_keyboard)


@router.callback_query(IsReply(), F.data == 'practice_zalivka')
@use_user_statistics
async def practice_zalivka(call: types.CallbackQuery, bot: Bot, state="*"):
    await call.answer()
    await bot.delete_message(chat_id = call.message.chat.id, message_id = call.message.message_id)
    max = await execute_select("select number from zalivka ORDER BY number DESC LIMIT 1")

    num = randint(5, max)
    photo_zalivka = await execute_select("select zalivka from zalivka where number = {}", (num,))

    await bot.send_photo(call.message.chat.id, photo = photo_zalivka,
                         caption = "Сосредоточьтесь и почувстуйте, что именно находится за заливкой.\n<code>При вызове нового задания ответ прошлого будет утерян, \nответ может узнать только тот, кто взял задание.</code>",
                         reply_markup = kb.practice_zalivka_keyboard)
    async with state.proxy() as data:
        data['zalivka_card'] = num


@router.callback_query(IsReply(), F.data == 'practice_zalivka_answer')
async def practice_zalivka_answer(call: types.CallbackQuery, bot: Bot, state="*"):
    await call.answer()
    try:
        async with state.proxy() as data:
            num = data['zalivka_card']
            photo_original = await execute_select("select zalivka_original from zalivka where number = {}", (num,))

            await bot.send_photo(call.message.chat.id, photo = photo_original)
            data['zalivka_card'] = None
    except Exception:
        return 0
