from aiogram import Router, Bot, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from database import execute_query, execute_select

CHAT_ID = -1001894916266

router = Router()


class Set(StatesGroup):
    rules = State()


async def create_tables():
    await execute_query(
        """
        CREATE TABLE IF NOT EXISTS users_chat (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            warns INTEGER DEFAULT 0,
            rep INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        ()
    )

    await execute_query(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL,
            rules TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        ()
    )


async def is_admin(message: Message, bot: Bot) -> bool:
    chat_id = message.chat.id
    user_id = message.from_user.id

    chat_member = await bot.get_chat_member(chat_id, user_id)
    return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]


@router.message(Command("unmute", "размут", prefix = "!"), F.chat.id == CHAT_ID)
async def unmute(message: Message, bot: Bot):
    if not await is_admin(message, bot):
        return

    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на сообщение!")
        return
    try:
        name = message.reply_to_message.from_user.full_name
        user_id = message.reply_to_message.from_user.id

        permissions = ChatPermissions(
            can_send_messages = True,
            can_send_media_messages = True,
            can_send_other_messages = True,
            can_add_web_page_previews = True
        )

        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions = permissions
        )
        await message.answer(f'[{name}] разблокирован.')
    except Exception as e:
        await message.reply(f"Попробуй !размут. Ошибка: {str(e)}")


@router.message(Command("unban", "разбан", prefix = "!"), F.chat.id == CHAT_ID)
async def unban(message: Message, bot: Bot):
    if not await is_admin(message, bot):
        return

    if not message.reply_to_message:
        await message.reply("Эта команда должна быть ответом на сообщение!")
        return
    try:
        name = message.reply_to_message.from_user.full_name
        user_id = message.reply_to_message.from_user.id
        await bot.unban_chat_member(message.chat.id, user_id)
        await message.answer(f'[{name}] разблокирован.')
    except Exception as e:
        await message.reply(f"Попробуй !разбан. Ошибка: {str(e)}")


@router.message(Command("mute", "мут", prefix = "!"), F.chat.id == CHAT_ID)
async def mute(message: Message, bot: Bot):
    if not await is_admin(message, bot):
        return

    try:
        if not message.reply_to_message:
            await message.reply("Эта команда должна быть ответом на сообщение!")
            return

        command_parts = message.text.split()
        if len(command_parts) < 3:
            await message.reply('Не хватает аргументов!\nПример:\n`!мут 1 ч причина`')
            return

        try:
            mute_duration = int(command_parts[1])
            mute_type = command_parts[2]
            comment = " ".join(command_parts[3:]) if len(command_parts) > 3 else "Не указана"
        except (IndexError, ValueError):
            await message.reply('Некорректные аргументы!\nПример:\n`!мут 1 ч причина`')
            return

        now = datetime.now()
        if mute_type in ["ч", "часов", "час"]:
            until_date = now + timedelta(hours = mute_duration)
        elif mute_type in ["м", "минут", "минуты"]:
            until_date = now + timedelta(minutes = mute_duration)
        elif mute_type in ["д", "дней", "день"]:
            until_date = now + timedelta(days = mute_duration)
        else:
            await message.reply('Некорректный тип времени! Используйте: м (минуты), ч (часы), д (дни)')
            return

        user_id = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.first_name

        mute_permissions = ChatPermissions(
            can_send_messages = False,
            can_send_media_messages = False,
            can_send_other_messages = False,
            can_add_web_page_previews = False
        )

        await bot.restrict_chat_member(
            chat_id = message.chat.id,
            user_id = user_id,
            permissions = mute_permissions,
            until_date = until_date
        )

        await message.reply(
            f'<b>Нарушитель:</b> <a href="tg://user?id={user_id}">{user_name}</a>\n'
            f'<b>Срок наказания:</b> {mute_duration} {mute_type}\n'
            f'<b>Причина:</b> {comment}',
            parse_mode = "HTML"
        )
    except Exception as e:
        await message.reply(f"Произошла ошибка при выполнении команды: {str(e)}")


@router.message(F.text.lower() == "установить правила")
async def set_rules_command(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin(message, bot):
        return

    await message.answer('Отправьте текст правил чата.')
    await state.set_state(Set.rules)


@router.message(Set.rules)
async def process_rules(message: Message, state: FSMContext):
    rules_text = message.text
    chat_id = message.chat.id

    try:
        result = await execute_select("SELECT rules FROM chats WHERE chat_id = $1", (chat_id,))

        if result:
            await execute_query(
                "UPDATE chats SET rules = $1 WHERE chat_id = $2",
                (rules_text, chat_id)
            )
        else:
            await execute_query(
                "INSERT INTO chats (chat_id, rules) VALUES ($1, $2)",
                (chat_id, rules_text)
            )

        await message.answer('Правила успешно установлены!')
    except Exception as e:
        await message.answer(f'Что-то пошло не так: {str(e)}')

    await state.clear()


@router.message(Command("warn", "варн", prefix = "!"), F.chat.id == CHAT_ID)
async def warn_user(message: Message, bot: Bot):
    if not await is_admin(message, bot):
        return

    if not message.reply_to_message:
        await message.reply("Отправь эту команду ответом на сообщение нарушителя.")
        return

    try:
        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.full_name

        result = await execute_select("SELECT warns FROM users_chat WHERE user_id = $1", (user_id,))

        if not result:
            await execute_query(
                "INSERT INTO users_chat (warns, user_id) VALUES ($1, $2)",
                (1, user_id)
            )
            await message.reply(f"Количество варнов у {username}: 1")
        else:
            current_warns = result['warns']
            if current_warns < 3:
                new_warns = current_warns + 1

                if new_warns < 3:
                    await execute_query(
                        "UPDATE users_chat SET warns = $1 WHERE user_id = $2",
                        (new_warns, user_id)
                    )
                    await message.reply(f"Количество варнов у {username}: {new_warns}")
                else:
                    try:
                        await execute_query("DELETE FROM users_chat WHERE warns = 2", ())

                        await bot.ban_chat_member(chat_id = message.chat.id, user_id = user_id)
                        await message.reply("Пока, дружок.")
                    except Exception as e:
                        await message.reply(f"{username} хоть и подонок, но исключить нельзя. Ошибка: {str(e)}")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")


@router.message(F.text.lower().endswith("!снять варн"), F.chat.id == CHAT_ID)
async def unwarn_user(message: Message, bot: Bot):
    if not await is_admin(message, bot):
        return

    if not message.reply_to_message:
        await message.answer("Отправь эту команду ответом на сообщение нарушителя.")
        return

    try:
        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.full_name

        result = await execute_select("SELECT warns FROM users_chat WHERE user_id = $1", (user_id,))

        if not result:
            await message.reply(f"У {username} нет варнов")
        else:
            current_warns = result['warns']
            if current_warns > 0:
                new_warns = current_warns - 1
                await execute_query(
                    "UPDATE users_chat SET warns = $1 WHERE user_id = $2",
                    (new_warns, user_id)
                )
                await message.reply(f"Количество варнов у {username}: {new_warns}")
            else:
                await message.reply(f"У {username} уже 0 варнов")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")


@router.message(Command("ban", "бан", prefix = "!"), F.chat.id == CHAT_ID)
async def ban_user(message: Message, bot: Bot):
    if not await is_admin(message, bot):
        return

    if not message.reply_to_message:
        await message.reply("Отправь эту команду ответом на сообщение нарушителя.")
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name

    try:

        await bot.ban_chat_member(chat_id = message.chat.id, user_id = user_id)
        await bot.delete_message(chat_id = message.chat.id, message_id = message.message_id)
        await bot.send_message(chat_id = message.chat.id, text = f"Дружок {user_name} забанен, радуемся.")
    except Exception as e:
        await message.reply(f"{user_name} хоть и подонок, но исключить нельзя. Ошибка: {str(e)}")
