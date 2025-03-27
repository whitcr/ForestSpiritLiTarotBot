from aiogram import types, Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import execute_select_all
from filters.baseFilters import IsReply
from filters.subscriptions import SubscriptionLevel
import keyboard as kb

router = Router()


@router.callback_query(F.data.startswith('get_practices_menu'), SubscriptionLevel(2))
async def practice_menu_cb(call: types.CallbackQuery):
    await call.message.edit_text(
        text = f"<b>Интуиция</b> — практики на развитие интуиции.\n\n"
               f"<b>Таро</b> — практики с картами Таро.\n\n"
               f"<b>Медитации</b> — список полезных медитаций.\n\n"
               f"<b>Практики</b> — различные эзотерические практики.",
        reply_markup = kb.practice_menu_general_keyboard)


@router.message(F.text.lower() == "практика", SubscriptionLevel(2))
async def practice_menu(message: types.Message):
    await message.reply(
        f"<b>Интуиция</b> — практики на развитие интуиции.\n\n"
        f"<b>Таро</b> — практики с картами Таро.\n\n"
        f"<b>Медитации</b> — список полезных медитаций.\n\n"
        f"<b>Практики</b> — различные эзотерические практики.", reply_markup = kb.practice_menu_general_keyboard)


@router.callback_query(IsReply(), F.data == 'practice_menu_practice')
async def practice_practices(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    try:
        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = f"Выберите тематику практик.",
                                    reply_markup = kb.practice_general_menu_practices_keyboard)
    except:
        return 0


@router.callback_query(IsReply(), F.data.startswith('practices_'))
async def process_callback_practices(call: types.CallbackQuery, bot: Bot):
    try:
        await call.answer()
        keyword = call.data.split('_')[1]
        practices = await execute_select_all(
            "SELECT name, text FROM practices_text WHERE keyword SIMILAR TO '%' || $1 || '%'",
            (keyword,)
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text = "Больше практик!", callback_data = f'show_practice_{1}_{keyword}')

        current_practices_index = 0
        current_practices = practices[current_practices_index]
        title = current_practices[0]
        description = current_practices[1]

        practice_message = f"<b>{title}:</b>\n\n{description}"

        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = practice_message,
                                    reply_markup = keyboard.as_markup())
    except Exception:
        pass


@router.callback_query(IsReply(), F.data.startswith('show_practice'))
async def process_callback_show_practice(call: types.CallbackQuery, bot: Bot):
    index = int(call.data.split('_')[2])
    keyword = call.data.split('_')[3]
    practices = await execute_select_all(
        "SELECT name, text FROM practices_text WHERE keyword SIMILAR TO '%' || $1 || '%'",
        (keyword,)
    )

    current_practice = practices[index]
    title = current_practice[0]
    description = current_practice[1]
    practice_message = f"<b>{title}:</b>\n\n{description}"

    keyboard = InlineKeyboardBuilder()

    if len(practices) == 1:
        pass
    elif index == 0:
        keyboard.button(text = '<--',
                        callback_data = f'show_practice_{len(practices) - 1}_{keyword}')
        keyboard.button(text = '-->', callback_data = f'show_practice_{index + 1}_{keyword}')
    elif index == len(practices) - 1:
        keyboard.button(text = '<--', callback_data = f'show_practice_{index - 1}_{keyword}')
        keyboard.button(text = '-->', callback_data = f'show_practice_0_{keyword}')
    else:
        keyboard.button(text = '<--', callback_data = f'show_practice_{index - 1}_{keyword}')
        keyboard.button(text = '-->', callback_data = f'show_practice_{index + 1}_{keyword}')

    keyboard.button(text = 'Меню', callback_data = f'get_practices_menu')

    keyboard.adjust(2)

    await bot.edit_message_text(chat_id = call.message.chat.id,
                                message_id = call.message.message_id,
                                text = practice_message,
                                reply_markup = keyboard.as_markup())
