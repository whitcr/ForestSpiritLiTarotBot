from aiogram import Router, F, types, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import load_config

router = Router()

config = load_config()
support_chat = config.tg_bot.support_chat


class SupportState(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()


@router.message(F.text.lower() == "помощь")
@router.callback_query(F.data == "get_support")
async def help_command(event: Message | CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text = "📝 Написать разработчику", callback_data = "ask_support")

    text = (
        "Если у вас есть какой-то вопрос, жалоба или предложение, "
        "вы можете написать разработчику. Нажмите кнопку и напишите. "
        "Только текст, никаких файлов.\n\n"
        "Список команд вы можете посмотреть тут — https://telegra.ph/Lesnoj-Duh-Li-10-10."
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup = keyboard.as_markup())
    elif isinstance(event, CallbackQuery):
        keyboard.button(text = "◀️ Назад в профиль", callback_data = "get_my_profile")
        keyboard.adjust(1)
        await event.message.edit_text(text, reply_markup = keyboard.as_markup())


@router.callback_query(F.data == "ask_support")
async def ask_question(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ваш запрос:")
    await state.set_state(SupportState.waiting_for_question)
    await callback.answer()


@router.message(SupportState.waiting_for_question)
async def receive_question(message: Message, bot: Bot, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = f"(@{message.from_user.username})" if message.from_user.username else ""

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text = "✉ Ответить", callback_data = f"reply_{user_id}")
    keyboard.button(text = "👤 Перейти в ЛС", url = f"tg://user?id={user_id}")

    await bot.send_message(
        support_chat,
        f"📩 *Новый запрос от {full_name}* {username}:\n\n"
        f"{message.text}",
        parse_mode = "Markdown",
        reply_markup = keyboard.as_markup(),
    )

    await message.answer("Ваш запрос отправлен. Ожидайте ответа.")


@router.callback_query(F.data.startswith("reply_"))
async def ask_admin_reply(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(user_id = user_id)
    await callback.message.answer("Введите ваш ответ:")
    await state.set_state(SupportState.waiting_for_answer)
    await callback.answer()


@router.message(SupportState.waiting_for_answer)
async def send_admin_reply(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    if not user_id:
        await message.answer("Ошибка: не найден ID пользователя.")
        return

    await state.clear()

    await bot.send_message(
        user_id,
        f"📬 *Ответ от поддержки:*\n\n{message.text}",
        parse_mode = "Markdown"
    )

    await message.answer("Ответ отправлен пользователю.")
