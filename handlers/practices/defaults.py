from aiogram import types, Router, F, Bot

from database import execute_select_all
from filters.baseFilters import IsReply
from filters.subscriptions import SubscriptionLevel
import keyboard as kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from middlewares.statsUser import UserStatisticsMiddleware

router = Router()
router.message.middleware(UserStatisticsMiddleware())
router.callback_query.middleware(UserStatisticsMiddleware())


@router.message(F.text.lower() == "практика", SubscriptionLevel(2), flags = {"use_user_statistics": True})
async def practice_menu(message: types.Message):
    await message.reply(
        f"<b>Интуиция</b> — практики на развитие интуиции.\n\n"
        f"<b>Таро</b> — практики с картами Таро.\n\n"
        f"<b>Медитации</b> — список полезных медитаций.\n\n"
        f"<b>Практики</b> — различные эзотерические практики.", reply_markup = kb.practice_menu_general_keyboard)


@router.callback_query(IsReply(), F.data == 'practice_menu_practice')
async def practice_practices(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    try:
        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = f"Выберите тематику практик.",
                                    reply_markup = kb.practice_general_menu_practices_keyboard)
    except:
        return 0


@router.callback_query(IsReply(), F.data.startswith('practices_'))
async def process_callback_practices(bot: Bot, call: types.CallbackQuery):
    try:
        await call.answer()
        keyword = call.data.split('_')[1]
        practices = await execute_select_all("SELECT name,text FROM practices_text WHERE keyword LIKE $1",
                                             ('%' + keyword + '%',))

        keyboard = InlineKeyboardMarkup()
        button_right = InlineKeyboardButton('Больше практик!', callback_data = f'show_practice_{1}_{keyword}')
        keyboard.add(button_right)

        current_practices_index = 0
        current_practices = practices[current_practices_index]
        title = current_practices[0]
        description = current_practices[1]

        practice_message = f"<b>{title}:</b>\n\n{description}"

        await bot.edit_message_text(chat_id = call.message.chat.id,
                                    message_id = call.message.message_id,
                                    text = practice_message,
                                    reply_markup = keyboard)
    except Exception:
        pass


@router.callback_query(IsReply(), F.data.startswith('show_practice'))
async def process_callback_show_practice(bot: Bot, call: types.CallbackQuery):
    await call.answer()
    try:
        if call.from_user.id == call.message.reply_to_message.from_user.id:
            index = int(call.data.split('_')[2])
            keyword = call.data.split('_')[3]
            practices = await execute_select_all("SELECT name, text FROM practices_text WHERE keyword LIKE $1",
                                                 ('%' + keyword + '%',))

            current_practice = practices[index]
            title = current_practice[0]
            description = current_practice[1]
            practice_message = f"<b>{title}:</b>\n\n{description}"

            keyboard = InlineKeyboardMarkup(row_width = 2)
            if len(practices) == 1:
                pass
            elif index == 0:
                button_right = InlineKeyboardButton('-->', callback_data = f'show_practice_{index + 1}_{keyword}')
                button_last = InlineKeyboardButton('<--',
                                                   callback_data = f'show_practice_{len(practices) - 1}_{keyword}')
                keyboard.row(button_last, button_right)
            elif index == len(practices) - 1:
                button_first = InlineKeyboardButton('-->', callback_data = f'show_practice_0_{keyword}')
                button_left = InlineKeyboardButton('<--', callback_data = f'show_practice_{index - 1}_{keyword}')
                keyboard.row(button_left, button_first)
            else:
                button_left = InlineKeyboardButton('<--', callback_data = f'show_practice_{index - 1}_{keyword}')
                button_right = InlineKeyboardButton('-->', callback_data = f'show_practice_{index + 1}_{keyword}')
                keyboard.row(button_left, button_right)

            await bot.edit_message_text(chat_id = call.message.chat.id,
                                        message_id = call.message.message_id,
                                        text = practice_message,
                                        reply_markup = keyboard)
    except Exception:
        pass
