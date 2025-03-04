import os
import time
from aiogram import types, F, Router, Bot
from aiogram.types import Message, InputFile

from database import execute_select_all, execute_query, execute_select
from filters.baseFilters import IsAdmin
from aiogram import F, Bot
from aiogram.types import Message

from functions.cards.create import get_buffered_image
from functions.statistics.globalStats import generate_stats_image

router = Router()


@router.message(IsAdmin(), F.text.startswith("кто"))
async def get_user(message: types.Message):
    user_id = message.text.split()[1]
    user = f"<a href='tg://user?id={user_id}'>чел</a>"
    text = f"Вот этот вот {user}"
    await message.reply(text)


@router.message(IsAdmin(), F.text.startswith("!всем"))
async def mailing(message: types.Message, bot: Bot, admin_id):
    parts = message.text.split()
    if len(parts) < 4:
        await message.reply("Usage: !всем <link> <wordlink> <message>")
        return

    link = parts[1]
    wordlink = parts[2]
    text_parts = parts[3:]
    llink = f"<a href='{link}'>{wordlink}</a>"
    post = f"— {llink} {' '.join(text_parts)}"

    ids = await execute_select_all("SELECT user_id FROM users")

    count_sent = 0
    count_blocked = 0

    for id_tuple in ids:
        user_id = id_tuple[0]
        try:
            await bot.send_message(user_id, post)
            count_sent += 1
            time.sleep(1)
        except Exception as e:
            count_blocked += 1
            await execute_query("DELETE FROM users WHERE user_id = $1", (user_id,))

    await bot.send_message(admin_id, f"Сообщение получили {count_sent} пользователя. {count_blocked} заблокировали Ли.")


@router.message(IsAdmin(), F.text.startswith("!!всем"))
async def mailing_1(message: types.Message, bot: Bot, admin_id):
    text_parts = message.text.split()[1:]
    post = f"— {' '.join(text_parts)}"

    ids = await execute_select_all("SELECT user_id FROM users LIMIT 20")

    count_sent = 0
    count_blocked = 0

    for id_tuple in ids:
        user_id = id_tuple[0]
        try:
            await bot.send_message(user_id, post)
            count_sent += 1
            time.sleep(1)
        except Exception as e:
            count_blocked += 1
            await execute_query("DELETE FROM users WHERE user_id = $1", (user_id,))

    await bot.send_message(admin_id,
                           f"Сообщение было отослано {count_sent} пользователям. {count_blocked} заблокировали Ли.")


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


@router.message(F.text.startswith("!статистика"))
async def cmd_stats(message: Message):
    stats = await execute_select_all(
        "SELECT command, daily_count, weekly_count, monthly_count, total_count FROM statistics_handler ORDER BY total_count DESC"
    )

    if stats:
        image = await generate_stats_image(stats)
        await message.answer_photo(photo = await get_buffered_image(image), caption = "Вот ваша статистика 📊")
    else:
        await message.answer("Статистика пока не собрана.")


@router.message(IsAdmin(), F.content_type.in_({'photo', 'video', 'document'}))
async def media_handler(message: Message, bot: Bot, logger_chat):
    if message.photo:
        media_id = message.photo[-1].file_id
    elif message.video:
        media_id = message.video.file_id
    elif message.document:
        media_id = message.document.file_id
    else:
        return

    await bot.send_message(logger_chat, f"Media ID: `{media_id}`", parse_mode = "Markdown")
