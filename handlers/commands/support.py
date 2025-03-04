from aiogram import Router, F, types, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from config import load_config

# Создаём router
router = Router()

config = load_config()
support_chat = config.tg_bot.support_chat


# Храним состояние пользователя (ожидание ввода запроса)
class SupportState(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()


# 📌 Команда "помощь" (работает ТОЛЬКО в ЛС бота)
@router.callback_query(F.data == "get_support")
async def help_command(call: CallbackQuery, bot: Bot):
    if call.message.chat.type == 'private':
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text = "📝 Написать разработчику", callback_data = "ask_support")
        await bot.send_message(call.from_user.id,
                               "Если у вас есть какой-то вопрос, жалоба или предложение, вы можете написать разработчику. Нажмите кнопку и напишите. "
                               "Только текст, никаких файлов. \n\n"
                               "Список команд вы можете посмотреть тут — https://telegra.ph/Lesnoj-Duh-Li-10-10.",
                               reply_markup = keyboard.as_markup())


# 📌 Пользователь нажал "Написать вопрос/жалобу"
@router.callback_query(F.data == "ask_support")
async def ask_question(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ваш запрос:")
    await state.set_state(SupportState.waiting_for_question)
    await callback.answer()


# 📌 Пользователь отправляет свой запрос
@router.message(SupportState.waiting_for_question)
async def receive_question(message: Message, bot: Bot, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = f"(@{message.from_user.username})" if message.from_user.username else ""

    # Кнопки для админа
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text = "✉ Ответить", callback_data = f"reply_{user_id}")
    keyboard.button(text = "👤 Перейти в ЛС", url = f"tg://user?id={user_id}")

    # Отправляем админу
    await bot.send_message(
        support_chat,
        f"📩 *Новый запрос от {full_name}* {username}:\n\n"
        f"{message.text}",
        parse_mode = "Markdown",
        reply_markup = keyboard.as_markup(),
    )

    await message.answer("Ваш запрос отправлен. Ожидайте ответа.")


# 📌 Админ нажал "Ответить"
@router.callback_query(F.data.startswith("reply_"))
async def ask_admin_reply(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])  # Получаем ID пользователя
    await state.update_data(user_id = user_id)  # Сохраняем ID пользователя
    await callback.message.answer("Введите ваш ответ:")
    await state.set_state(SupportState.waiting_for_answer)
    await callback.answer()


# 📌 Админ отправляет ответ
@router.message(SupportState.waiting_for_answer)
async def send_admin_reply(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    if not user_id:
        await message.answer("Ошибка: не найден ID пользователя.")
        return

    await state.clear()

    # Отправляем ответ пользователю
    await bot.send_message(
        user_id,
        f"📬 *Ответ от поддержки:*\n\n{message.text}",
        parse_mode = "Markdown"
    )

    await message.answer("Ответ отправлен пользователю.")
