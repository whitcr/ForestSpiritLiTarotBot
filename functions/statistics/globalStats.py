from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData

from database import execute_select_all

router = Router()


class StatsCallback(CallbackData, prefix = "stats"):
    stats_type: str  # 'commands', 'cards', 'users'
    page: int


def format_stats(stats, page: int, stats_type: str, page_size: int = 10):
    total_pages = (len(stats) + page_size - 1) // page_size
    start, end = page * page_size, (page + 1) * page_size
    paginated_stats = stats[start:end]

    titles = {
        "commands": "📊 <b>Статистика команд</b>\n\n",
        "cards": "🎴 <b>Статистика карт</b>\n\n",
        "users": "👤 <b>Статистика пользователей</b>\n\n"
    }
    text = titles.get(stats_type, "📊 <b>Статистика</b>\n\n")

    for stat in paginated_stats:
        if stats_type == "users":
            user_link = f'<a href="tg://user?id={stat[0]}">{stat[0]}</a>'
            text += f"👤 Пользователь: {user_link}\n"
        else:
            text += f"✅ <b>{stat[0]}</b>\n"

        text += f"📅 Д: {stat[1]} | 📆 Н: {stat[2]} | 🗓 М: {stat[3]} | 🔥 Всего: {stat[4]}\n\n"

    return text, total_pages


def get_stats_keyboard(stats_type: str, page: int, total_pages: int):
    keyboard = InlineKeyboardBuilder()
    if page > 0:
        keyboard.button(text = "⏪ Назад", callback_data = StatsCallback(stats_type = stats_type, page = page - 1))
    if page < total_pages - 1:
        keyboard.button(text = "Вперёд ⏩", callback_data = StatsCallback(stats_type = stats_type, page = page + 1))
    keyboard.adjust(1)
    return keyboard.as_markup()


async def show_statistics(callback: types.CallbackQuery, stats_type: str, bot):
    table_name = {
        "commands": "statistics_handler",
        "cards": "statistics_cards",
        "users": "users"
    }.get(stats_type)

    column_name = "command" if stats_type == "commands" else "card" if stats_type == "cards" else "user_id"

    stats = await execute_select_all(
        f"SELECT {column_name}, daily_count, weekly_count, monthly_count, total_count "
        f"FROM {table_name} "
        f"WHERE daily_count IS NOT NULL AND weekly_count IS NOT NULL AND monthly_count IS NOT NULL AND total_count IS NOT NULL "
        f"ORDER BY daily_count DESC"
    )

    if stats:
        page = 0
        text, total_pages = format_stats(stats, page, stats_type)
        keyboard = get_stats_keyboard(stats_type, page, total_pages)

        await bot.send_message(callback.message.chat.id, text, reply_markup = keyboard, parse_mode = "HTML")
    else:
        await callback.message.answer("Статистика пока не собрана.")

    await callback.answer()


@router.callback_query(StatsCallback.filter())
async def paginate_stats(callback: CallbackQuery, callback_data: StatsCallback):
    table_name = {
        "commands": "statistics_handler",
        "cards": "statistics_cards",
        "users": "users"
    }.get(callback_data.stats_type)

    column_name = "command" if callback_data.stats_type == "commands" else "card" if callback_data.stats_type == "cards" else "user_id"

    stats = await execute_select_all(
        f"SELECT {column_name}, daily_count, weekly_count, monthly_count, total_count FROM {table_name} ORDER BY daily_count DESC"
    )

    page = callback_data.page
    text, total_pages = format_stats(stats, page, callback_data.stats_type)
    keyboard = get_stats_keyboard(callback_data.stats_type, page, total_pages)

    await callback.message.edit_text(text, reply_markup = keyboard, parse_mode = "HTML")
