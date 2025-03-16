import asyncio
import logging
import random
from datetime import datetime
from typing import List

from aiogram import Bot, Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from database import execute_query, execute_select, execute_select_all
from filters.baseFilters import IsAdmin
from functions.contest.contest import get_valid_referrals_count, check_subscription

router = Router()


class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_broadcast_file = State()
    waiting_for_prize_description = State()
    waiting_for_referral_prize = State()
    waiting_for_min_referrals = State()
    waiting_for_winners_count = State()
    waiting_for_end_date = State()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text = "📣 Сделать рассылку", callback_data = "admin_broadcast"))
    builder.add(InlineKeyboardButton(text = "⚙️ Настройки конкурса", callback_data = "admin_settings"))
    builder.add(InlineKeyboardButton(text = "📊 Статистика", callback_data = "admin_stats"))
    builder.add(InlineKeyboardButton(text = "🏆 Выбрать победителей", callback_data = "admin_winners"))
    builder.add(InlineKeyboardButton(text = "🔄 Завершить конкурс", callback_data = "admin_end_contest"))

    builder.adjust(1)
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text = "🏆 Описание основного приза", callback_data = "settings_prize"))
    builder.add(InlineKeyboardButton(text = "🎁 Описание реферального приза", callback_data = "settings_ref_prize"))
    builder.add(InlineKeyboardButton(text = "👥 Мин. количество рефералов", callback_data = "settings_min_refs"))
    builder.add(InlineKeyboardButton(text = "👑 Количество победителей", callback_data = "settings_winners_count"))
    builder.add(InlineKeyboardButton(text = "📅 Дата окончания конкурса", callback_data = "settings_end_date"))
    builder.add(InlineKeyboardButton(text = "◀️ Назад", callback_data = "admin_menu"))

    builder.adjust(1)
    return builder.as_markup()


def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text = "📝 Текст сообщения", callback_data = "broadcast_text"))
    builder.add(InlineKeyboardButton(text = "📎 Добавить файл", callback_data = "broadcast_file"))
    builder.add(InlineKeyboardButton(text = "✅ Отправить", callback_data = "broadcast_send"))
    builder.add(InlineKeyboardButton(text = "❌ Отмена", callback_data = "admin_menu"))

    builder.adjust(1)
    return builder.as_markup()


async def select_winners(count: int) -> List[int]:
    all_participants = await execute_select_all("SELECT user_id FROM contest_users")

    if not all_participants:
        return []

    user_ids = [row[0] for row in all_participants]

    winners_count = min(count, len(user_ids))
    winners = random.sample(user_ids, winners_count)

    return winners


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "❌ Отмена", callback_data = "admin_menu"))
    return builder.as_markup()


@router.message(IsAdmin(), Command("admin"))
async def admin_command(message: types.Message):
    await message.answer(
        "👑 Панель управления конкурсом",
        reply_markup = get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👑 Панель управления конкурсом",
        reply_markup = get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_settings")
async def admin_settings_callback(callback: types.CallbackQuery):
    settings = await execute_select_all(
        "SELECT prize_description, referral_prize_description, min_referrals, winners_count, ends_at, is_active FROM contest_settings ORDER BY id DESC LIMIT 1")

    if settings:
        prize, ref_prize, min_refs, winners, ends_at, is_active = settings[0]
        status = "Активен ✅" if is_active else "Неактивен ❌"
        end_date = ends_at.strftime("%d.%m.%Y") if ends_at else "Не указана"
    else:
        prize = "Not set"
        ref_prize = "Not set"
        min_refs = 3
        winners = 1
        end_date = "Не указана"
        status = "Неактивен ❌"

    await callback.message.edit_text(
        f"⚙️ Настройки конкурса\n\n"
        f"Статус конкурса: {status}\n"
        f"Описание приза: {prize}\n"
        f"Реферальный приз: {ref_prize}\n"
        f"Мин. кол-во рефералов: {min_refs}\n"
        f"Кол-во победителей: {winners}\n"
        f"Дата окончания: {end_date}\n\n"
        f"Выберите настройку для изменения:",
        reply_markup = get_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery, bot: Bot):
    total_users = await execute_select("SELECT COUNT(*) FROM contest_users WHERE ticket_number IS NOT NULL")
    total_users = total_users if total_users else 0

    valid_referrers = 0
    settings = await execute_select("SELECT min_referrals FROM contest_settings ORDER BY id DESC LIMIT 1")
    min_referrals = settings if settings else 3

    all_users = await execute_select_all("SELECT user_id FROM contest_users WHERE ticket_number IS NOT NULL")
    for user_row in all_users:
        user_id = user_row[0]
        valid_count = await get_valid_referrals_count(user_id, bot)
        if valid_count >= min_referrals:
            valid_referrers += 1

        top_referrers = []
        top_referrers_data = await execute_select_all(
            """
            SELECT u.user_id, u.username, u.first_name, COUNT(r.user_id) as ref_count
            FROM contest_users u
            LEFT JOIN contest_users r ON u.user_id = r.referrer_id
            WHERE u.ticket_number IS NOT NULL
            GROUP BY u.user_id, u.username, u.first_name
            ORDER BY ref_count DESC
            LIMIT 5
            """
        )

        for row in top_referrers_data:
            user_id, username, first_name, ref_count = row
            if ref_count > 0:
                display_name = f"@{username}" if username else first_name
                top_referrers.append(f"{display_name}: {ref_count} приглашений")

        top_referrers_text = "\n".join(top_referrers) if top_referrers else "Нет данных"

        unsubscribed_count = 0
        for user_row in all_users:
            user_id = user_row[0]
            if not await check_subscription(user_id, bot):
                unsubscribed_count += 1

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text = "◀️ Назад", callback_data = "admin_menu"))

        await callback.message.edit_text(
            f"📊 Статистика конкурса\n\n"
            f"Всего участников: {total_users}\n"
            f"Участников с призами за рефералов: {valid_referrers}\n"
            f"Отписавшихся участников: {unsubscribed_count}\n\n"
            f"Топ 5 по приглашениям:\n{top_referrers_text}",
            reply_markup = builder.as_markup()
        )
        await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text(
        "📣 Создание рассылки для участников конкурса\n\n"
        "Выберите что вы хотите добавить в рассылку:",
        reply_markup = get_broadcast_keyboard()
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "broadcast_text")
async def broadcast_text_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_broadcast_text)

    await callback.message.edit_text(
        "📝 Введите текст сообщения для рассылки:",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_broadcast_text))
async def process_broadcast_text(message: types.Message, state: FSMContext):
    await state.update_data(broadcast_text = message.text)
    await state.set_state(None)

    await message.answer(
        f"✅ Текст сообщения установлен:\n\n{message.text}\n\nВыберите следующее действие:",
        reply_markup = get_broadcast_keyboard()
    )


@router.callback_query(IsAdmin(), F.data == "broadcast_file")
async def broadcast_file_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_broadcast_file)

    await callback.message.edit_text(
        "📎 Отправьте файл для рассылки (фото, видео, документ):",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_broadcast_file))
async def process_broadcast_file(message: types.Message, state: FSMContext):
    file_id = None
    file_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.animation:
        file_id = message.animation.file_id
        file_type = "animation"

    if file_id:
        await state.update_data(broadcast_file_id = file_id, broadcast_file_type = file_type)
        await state.set_state(None)

        await message.answer(
            f"✅ Файл ({file_type}) добавлен к рассылке. Выберите следующее действие:",
            reply_markup = get_broadcast_keyboard()
        )
    else:
        await message.answer(
            "❌ Не удалось распознать файл. Попробуйте еще раз или отмените действие.",
            reply_markup = get_cancel_keyboard()
        )


@router.callback_query(IsAdmin(), F.data == "broadcast_send")
async def broadcast_send_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    broadcast_text = data.get("broadcast_text", "")
    file_id = data.get("broadcast_file_id")
    file_type = data.get("broadcast_file_type")

    if not broadcast_text and not file_id:
        await callback.answer("Необходимо добавить текст или файл для рассылки!", show_alert = True)
        return

    all_users = await execute_select_all("SELECT user_id FROM contest_users WHERE ticket_number IS NOT NULL")

    if not all_users:
        await callback.answer("Нет участников для рассылки!", show_alert = True)
        return

    await execute_query(
        "INSERT INTO contest_messages (message_text, file_id, file_type) VALUES ($1,$2, $3)",
        (broadcast_text, file_id, file_type)
    )

    await callback.message.edit_text("📤 Рассылка начата... Это может занять некоторое время.")

    success_count = 0
    fail_count = 0

    for user_row in all_users:
        user_id = user_row[0]
        try:
            if file_id:
                if file_type == "photo":
                    await bot.send_photo(user_id, photo = file_id, caption = broadcast_text)
                elif file_type == "video":
                    await bot.send_video(user_id, video = file_id, caption = broadcast_text)
                elif file_type == "document":
                    await bot.send_document(user_id, document = file_id, caption = broadcast_text)
                elif file_type == "animation":
                    await bot.send_animation(user_id, animation = file_id, caption = broadcast_text)
            else:
                await bot.send_message(user_id, broadcast_text)

            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {e}")
            fail_count += 1

    await callback.message.edit_text(
        f"📤 Рассылка завершена!\n\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удалось отправить: {fail_count}",
        reply_markup = get_admin_keyboard()
    )

    await state.clear()
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_winners")
async def admin_winners_callback(callback: types.CallbackQuery):
    settings = await execute_select_all(
        "SELECT winners_count, is_active FROM contest_settings ORDER BY id DESC LIMIT 1")

    if not settings:
        await callback.answer("Настройки конкурса не найдены!", show_alert = True)
        return

    winners_count, is_active = settings[0]

    if is_active:
        await callback.answer("Конкурс еще активен! Завершите его перед выбором победителей.", show_alert = True)
        return

    winners = await select_winners(winners_count)

    if not winners:
        await callback.answer("Нет участников для выбора победителей!", show_alert = True)
        return

    winners_text = ""
    for i, winner_id in enumerate(winners, 1):
        winner_info = await execute_select(
            "SELECT username, first_name, ticket_number FROM contest_users WHERE user_id = %s",
            (winner_id,)
        )

        if winner_info:
            username, first_name, ticket = winner_info
            display_name = f"@{username}" if username else first_name
            winners_text += f"{i}. {display_name} (Билет #{ticket})\n"

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "🔄 Выбрать заново", callback_data = "admin_winners"))
    builder.add(InlineKeyboardButton(text = "◀️ Назад", callback_data = "admin_menu"))
    builder.adjust(1)

    await callback.message.edit_text(
        f"🏆 Победители конкурса:\n\n{winners_text}\n\n"
        f"Поздравляем победителей! Вы можете связаться с ними, чтобы вручить призы.",
        reply_markup = builder.as_markup()
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "admin_end_contest")
async def admin_end_contest_callback(callback: types.CallbackQuery):
    status = await execute_select("SELECT is_active FROM contest_settings ORDER BY id DESC LIMIT 1")

    if not status:
        await callback.answer("Конкурс уже завершен!", show_alert = True)
        return

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text = "✅ Да, завершить", callback_data = "confirm_end_contest"))
    builder.add(InlineKeyboardButton(text = "❌ Нет, отмена", callback_data = "admin_menu"))
    builder.adjust(1)

    await callback.message.edit_text(
        "🚫 Вы уверены, что хотите завершить конкурс?\n\n"
        "После завершения текущего конкурса, вы сможете выбрать победителей и начать новый конкурс.",
        reply_markup = builder.as_markup()
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "confirm_end_contest")
async def confirm_end_contest_callback(callback: types.CallbackQuery, bot: Bot):
    await execute_query(
        "UPDATE contest_settings SET is_active = FALSE, ends_at = $1 WHERE id = (SELECT id FROM contest_settings ORDER BY id DESC LIMIT 1)",
        (datetime.now(),)
    )

    all_users = await execute_select_all("SELECT user_id FROM contest_users WHERE ticket_number IS NOT NULL")

    for user_row in all_users:
        try:
            await bot.send_message(
                user_row[0],
                "🏁 Конкурс завершен! Скоро будут объявлены победители. Спасибо за участие!"
            )
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Failed to notify user {user_row[0]}: {e}")

    await callback.message.edit_text(
        "✅ Конкурс успешно завершен!\n\n"
        "Теперь вы можете выбрать победителей.",
        reply_markup = get_admin_keyboard()
    )
    await callback.answer()


# Settings handlers
@router.callback_query(IsAdmin(), F.data == "settings_prize")
async def settings_prize_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_prize_description)

    await callback.message.edit_text(
        "🏆 Введите описание основного приза конкурса:",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_prize_description))
async def process_prize_description(message: types.Message, state: FSMContext):
    await execute_query(
        "UPDATE contest_settings SET prize_description = $1 WHERE id = (SELECT id FROM contest_settings ORDER BY id DESC LIMIT 1)",
        (message.text,)
    )

    await state.clear()
    await message.answer(
        f"✅ Описание приза установлено:\n\n{message.text}",
        reply_markup = get_settings_keyboard()
    )


@router.callback_query(IsAdmin(), F.data == "settings_ref_prize")
async def settings_ref_prize_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_referral_prize)

    await callback.message.edit_text(
        "🎁 Введите описание приза за приглашение друзей:",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_referral_prize))
async def process_referral_prize(message: types.Message, state: FSMContext):
    await execute_query(
        "UPDATE contest_settings SET referral_prize_description = $1 WHERE id = (SELECT id FROM contest_settings ORDER BY id DESC LIMIT 1)",
        (message.text,)
    )

    await state.clear()
    await message.answer(
        f"✅ Описание реферального приза установлено:\n\n{message.text}",
        reply_markup = get_settings_keyboard()
    )


@router.callback_query(IsAdmin(), F.data == "settings_min_refs")
async def settings_min_refs_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_min_referrals)

    await callback.message.edit_text(
        "👥 Введите минимальное количество рефералов для получения приза (число):",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_min_referrals))
async def process_min_referrals(message: types.Message, state: FSMContext):
    try:
        min_refs = int(message.text)
        if min_refs < 1:
            await message.answer("❌ Значение должно быть больше 0. Попробуйте еще раз:")
            return

        await execute_query(
            "UPDATE contest_settings SET min_referrals = %s WHERE id = (SELECT id FROM contest_settings ORDER BY id DESC LIMIT 1)",
            (min_refs,)
        )

        await state.clear()
        await message.answer(
            f"✅ Минимальное количество рефералов установлено: {min_refs}",
            reply_markup = get_settings_keyboard()
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число:")


@router.callback_query(IsAdmin(), F.data == "settings_winners_count")
async def settings_winners_count_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_winners_count)

    await callback.message.edit_text(
        "👑 Введите количество победителей конкурса (число):",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_winners_count))
async def process_winners_count(message: types.Message, state: FSMContext):
    try:
        winners_count = int(message.text)
        if winners_count < 1:
            await message.answer("❌ Значение должно быть больше 0. Попробуйте еще раз:")
            return

        await execute_query(
            "UPDATE contest_settings SET winners_count = $1 WHERE id = (SELECT id FROM contest_settings ORDER BY id DESC LIMIT 1)",
            (winners_count,)
        )

        await state.clear()
        await message.answer(
            f"✅ Количество победителей установлено: {winners_count}",
            reply_markup = get_settings_keyboard()
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число:")


@router.callback_query(IsAdmin(), F.data == "settings_end_date")
async def settings_end_date_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_end_date)

    await callback.message.edit_text(
        "📅 Введите дату окончания конкурса в формате ДД.ММ.ГГГГ:",
        reply_markup = get_cancel_keyboard()
    )
    await callback.answer()


@router.message(IsAdmin(), StateFilter(AdminStates.waiting_for_end_date))
async def process_end_date(message: types.Message, state: FSMContext):
    try:
        end_date = datetime.strptime(message.text, "%d.%m.%Y")

        await execute_query(
            "UPDATE contest_settings SET ends_at = $1 WHERE id = (SELECT id FROM contest_settings ORDER BY id DESC LIMIT 1)",
            (end_date,)
        )

        await state.clear()
        await message.answer(
            f"✅ Дата окончания конкурса установлена: {end_date.strftime('%d.%m.%Y')}",
            reply_markup = get_settings_keyboard()
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")
