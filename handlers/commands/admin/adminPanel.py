import time
from aiogram import types, F, Router, Bot
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import execute_select_all, execute_query
from filters.baseFilters import IsAdmin
from functions.statistics.globalStats import show_statistics

router = Router()


class AdminStates(StatesGroup):
    waiting_for_mailing = State()
    waiting_for_mailing_confirm = State()
    waiting_for_user_id = State()


def get_admin_keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text = "📊 Команды", callback_data = "admin_statistics_handlers"),
        InlineKeyboardButton(text = "📊 Карты", callback_data = "admin_statistics_cards"),
        InlineKeyboardButton(text = "📊 Пользователи", callback_data = "admin_statistics_users"),
        InlineKeyboardButton(text = "📣 Рассылка всем", callback_data = "admin_mailing"),
        InlineKeyboardButton(text = "🔍 Узнать по айди", callback_data = "admin_get_by_id"),
        InlineKeyboardButton(text = "🆔 Узнать айди медиа", callback_data = "admin_get_id")
    )

    builder.adjust(2)

    return builder.as_markup()


def get_mailing_keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text = "◀️ Назад в меню", callback_data = "admin_back_to_menu")
    )

    builder.adjust(1)

    return builder.as_markup()


def get_confirm_mailing_keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text = "✅ Подтвердить отправку", callback_data = "confirm_mailing"),
        InlineKeyboardButton(text = "❌ Отменить", callback_data = "cancel_mailing")
    )

    builder.adjust(1)

    return builder.as_markup()


@router.message(IsAdmin(), Command("пан"))
async def admin_panel(message: Message):
    await message.answer("Панель администратора активирована:", reply_markup = get_admin_keyboard())


@router.callback_query(IsAdmin(), F.data == "admin_statistics_handlers")
async def show_statistics_handlers(callback: types.CallbackQuery, bot: Bot):
    await show_statistics(callback, "commands", bot)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_statistics_cards")
async def show_statistics_cards(callback: types.CallbackQuery, bot: Bot):
    await show_statistics(callback, "cards", bot)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_statistics_users")
async def show_users_statistics(callback: types.CallbackQuery, bot: Bot):
    await show_statistics(callback, "users", bot)


@router.callback_query(IsAdmin(), F.data == "admin_mailing")
async def show_mailing_options(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_mailing)
    await callback.message.edit_text(
        "📣 Режим рассылки активирован.\n\n"
        "Отправьте сообщение для рассылки всем пользователям.\n"
        "Вы можете прикрепить фото, видео или документ к сообщению.\n\n"
        "Для добавления ссылки используйте HTML-формат:\n"
        "<pre>&lt;a href='URL'&gt; текст ссылки &lt;/a&gt;</pre>",
        parse_mode = "HTML",
        reply_markup = get_mailing_keyboard()
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_back_to_menu")
async def back_to_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Панель администратора:", reply_markup = get_admin_keyboard())
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_get_by_id")
async def get_by_id(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_user_id)
    await callback.message.answer("Отправьте ID пользователя, чтобы получить на него ссылку:")
    await callback.answer()


@router.message(IsAdmin(), AdminStates.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        user_info = await execute_select_all("SELECT * FROM users WHERE user_id = $1", (user_id,))

        if user_info:
            user_link = f"<a href='tg://user?id={user_id}'>Пользователь {user_id}</a>"
            username = user_info[0].get("username", "Нет username")
            first_name = user_info[0].get("first_name", "Нет имени")

            text = f"Информация о пользователе:\n\n"\
                   f"🆔 ID: {user_id}\n"\
                   f"👤 Имя: {first_name}\n"\
                   f"🔗 Username: @{username}\n"\
                   f"📱 Ссылка: {user_link}"
        else:
            text = f"Пользователь с ID {user_id} не найден в базе данных.\n"\
                   f"Ссылка: <a href='tg://user?id={user_id}'>Пользователь {user_id}</a>"

        await message.reply(text, parse_mode = "HTML")
    except ValueError:
        await message.reply("Пожалуйста, отправьте корректный числовой ID пользователя.")

    await state.clear()
    await message.answer("Панель администратора:", reply_markup = get_admin_keyboard())


@router.callback_query(IsAdmin(), F.data == "admin_get_id")
async def get_media_id_mode(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Режим получения ID активирован.\n"
        "Отправьте медиафайл (фото, видео или документ), чтобы получить его ID."
    )
    await callback.answer()


@router.message(IsAdmin(), AdminStates.waiting_for_mailing, F.content_type.in_({'text', 'photo', 'video', 'document'}))
async def process_mailing_message(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(message_id = message.message_id)

    media_type = None
    media_id = None
    caption = None

    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
        caption = message.caption or ""
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id
        caption = message.caption or ""
    elif message.document:
        media_type = "document"
        media_id = message.document.file_id
        caption = message.caption or ""
    else:
        media_type = "text"
        caption = message.text

    await state.update_data(
        media_type = media_type,
        media_id = media_id,
        caption = caption
    )

    preview_text = "📣 Предпросмотр сообщения для рассылки:\n\n"

    if media_type == "text":
        await message.reply(
            f"{preview_text}{caption}",
            reply_markup = get_confirm_mailing_keyboard(),
            parse_mode = "HTML"
        )
    elif media_type == "photo":
        await bot.send_photo(message.from_user.id, photo = media_id, caption = caption, parse_mode = "HTML")

    elif media_type == "video":
        await bot.send_video(message.from_user.id, video = media_id, caption = caption, parse_mode = "HTML")

    elif media_type == "document":
        await bot.send_document(message.from_user.id, document = media_id, caption = caption, parse_mode = "HTML")

    await message.reply(
        f"Меню",
        reply_markup = get_confirm_mailing_keyboard()
    )

    await state.set_state(AdminStates.waiting_for_mailing_confirm)


@router.callback_query(IsAdmin(), AdminStates.waiting_for_mailing_confirm, F.data == "confirm_mailing")
async def confirm_mailing(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    caption = data.get("caption")

    await callback.message.edit_text("🔄 Рассылка началась. Пожалуйста, подождите...")

    users = await execute_select_all("SELECT user_id FROM users")

    count_sent = 0
    count_blocked = 0

    for user_tuple in users:
        user_id = user_tuple[0]
        try:
            if media_type == "text":
                await bot.send_message(user_id, caption, parse_mode = "HTML")
            elif media_type == "photo":
                await bot.send_photo(user_id, photo = media_id, caption = caption, parse_mode = "HTML")
            elif media_type == "video":
                await bot.send_video(user_id, video = media_id, caption = caption, parse_mode = "HTML")
            elif media_type == "document":
                await bot.send_document(user_id, document = media_id, caption = caption, parse_mode = "HTML")

            count_sent += 1
            time.sleep(0.1)
        except Exception as e:
            count_blocked += 1
            await execute_query("DELETE FROM users WHERE user_id = $1", (user_id,))

    await callback.message.edit_text(
        f"✅ Рассылка завершена!\n\n"
        f"📊 Статистика:\n"
        f"- Успешно отправлено: {count_sent}\n"
        f"- Не получили сообщение: {count_blocked}"
    )

    await state.clear()
    await callback.message.answer("Панель администратора:", reply_markup = get_admin_keyboard())


@router.callback_query(IsAdmin(), AdminStates.waiting_for_mailing_confirm, F.data == "cancel_mailing")
async def cancel_mailing(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена")
    await callback.message.answer("Панель администратора:", reply_markup = get_admin_keyboard())


@router.message(IsAdmin(), F.content_type.in_({'photo', 'video', 'document'}))
async def media_handler(message: Message, state: FSMContext):
    if await state.get_state() is not None:
        return

    if message.photo:
        media_id = message.photo[-1].file_id
    elif message.video:
        media_id = message.video.file_id
    elif message.document:
        media_id = message.document.file_id
    else:
        return

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text = "Вернуться в меню", callback_data = "admin_back_to_menu")
    )
    builder.adjust(1)

    await message.reply(
        f"Вы можете скопировать этот ID для повторного использования. \n\n "
        f"<code>{media_id}</code>",
        parse_mode = "HTML",
        reply_markup = builder.as_markup()
    )


@router.message(IsAdmin(), F.text.lower() == "пока, дружок")
async def get_ban(message: types.Message, bot: Bot):
    if message.chat.type in ['group', 'supergroup']:
        if not message.reply_to_message:
            await message.reply("Отправь эту команду ответом на сообщение нарушителя.")
        else:
            try:
                replied_user = message.reply_to_message.from_user.id
                name_user = message.reply_to_message.from_user.first_name
                await bot.ban_chat_member(chat_id = message.chat.id, user_id = replied_user)
                await bot.send_message(chat_id = message.chat.id, text = f"Дружок {name_user} забанен, радуемся.")
            except Exception as e:
                await message.reply(f"Не удалось забанить пользователя: {e}")
