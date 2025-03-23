import io
import datetime
from datetime import datetime

from aiogram import Router, F
from aiogram import types
from database import execute_select_all

logger_chat_id = -4705330532

router = Router()


async def export_statistics_to_log(bot, stats_type: str, period_type: str):
    table_name = {
        "commands": "statistics_handler",
        "cards": "statistics_cards",
        "users": "users"
    }.get(stats_type)

    column_name = "command" if stats_type == "commands" else "card" if stats_type == "cards" else "user_id"
    period_column = f"{period_type}_count"

    current_date = datetime.now().strftime("%Y-%m-%d")

    query = f"""
    SELECT {column_name}, {period_column}
    FROM {table_name}
    WHERE {period_column} IS NOT NULL
    ORDER BY {period_column} DESC
    """

    stats = await execute_select_all(query)

    if not stats:
        await bot.send_message(logger_chat_id, f"Нет данных для {stats_type} {period_type}")
        return

    headers = {
        "commands": f"📊 Статистика команд за {period_type} период ({current_date})",
        "cards": f"🎴 Статистика карт за {period_type} период ({current_date})",
        "users": f"👤 Статистика пользователей за {period_type} период ({current_date})"
    }

    header_text = headers.get(stats_type, f"📊 Статистика {stats_type} за {period_type} период ({current_date})")

    file_content = f"{header_text}\n\n"

    for i, stat in enumerate(stats, 1):
        identifier = stat[0]
        count = stat[1]

        if stats_type == "users":
            file_content += f"{i}. Пользователь: {identifier}, Использований: {count}\n"
        elif stats_type == "commands":
            file_content += f"{i}. Команда: {identifier}, Использований: {count}\n"
        elif stats_type == "cards":
            file_content += f"{i}. Карта: {identifier}, Использований: {count}\n"

    file_buffer = io.BytesIO(file_content.encode('utf-8'))

    file = types.BufferedInputFile(
        file_buffer.getvalue(),
        filename = f"{current_date}_{stats_type}_{period_type}.txt"
    )

    await bot.send_document(
        logger_chat_id,
        document = file,
        caption = f"📊 Полная статистика {stats_type} за {period_type} период ({current_date})"
    )

    message_text = f"<b>{header_text}</b>\n\n"

    message_text += "<b>🥇 ТОП-3 по активности:</b>\n"
    for i, stat in enumerate(stats[:3], 1):
        identifier = stat[0]
        count = stat[1]

        if stats_type == "users":
            user_link = f'<a href="tg://user?id={identifier}">{identifier}</a>'
            message_text += f"{i}. 👤 Пользователь: {user_link}, Использований: {count}\n"
        elif stats_type == "commands":
            message_text += f"{i}. 💬 Команда: <code>{identifier}</code>, Использований: {count}\n"
        elif stats_type == "cards":
            message_text += f"{i}. 🎴 Карта: <code>{identifier}</code>, Использований: {count}\n"

    if len(stats) > 6:
        message_text += "\n<b>🔻 Последние 3 по активности:</b>\n"
        for i, stat in enumerate(stats[-3:], len(stats) - 2):
            identifier = stat[0]
            count = stat[1]

            if stats_type == "users":
                user_link = f'<a href="tg://user?id={identifier}">{identifier}</a>'
                message_text += f"{i}. 👤 Пользователь: {user_link}, Использований: {count}\n"
            elif stats_type == "commands":
                message_text += f"{i}. 💬 Команда: <code>{identifier}</code>, Использований: {count}\n"
            elif stats_type == "cards":
                message_text += f"{i}. 🎴 Карта: <code>{identifier}</code>, Использований: {count}\n"

    await bot.send_message(logger_chat_id, message_text, parse_mode = "HTML")

    total_actions = sum(stat[1] for stat in stats)
    summary = f"🔄 Итого {len(stats)} {stats_type} с общим количеством {total_actions} действий за {period_type} период."
    await bot.send_message(logger_chat_id, summary)


async def export_daily_stats(bot):
    for stats_type in ["commands", "cards", "users"]:
        await export_statistics_to_log(bot, stats_type, "daily")


async def export_weekly_stats(bot):
    for stats_type in ["commands", "cards", "users"]:
        await export_statistics_to_log(bot, stats_type, "weekly")


async def export_monthly_stats(bot):
    for stats_type in ["commands", "cards", "users"]:
        await export_statistics_to_log(bot, stats_type, "monthly")
