from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatMemberStatus
from aiogram.utils.keyboard import InlineKeyboardBuilder
import re
import asyncio
from constants import CARDS_NAME_SYNONYMS, CARDS
from database import execute_query, execute_select

router = Router()
CARDS = set(CARDS)
CHAT_ID = -1001928497656


async def create_tables():
    await execute_query(
        """CREATE TABLE IF NOT EXISTS meaning_chat (
            num SERIAL PRIMARY KEY,
            cards TEXT,
            situation TEXT,
            meaningCards TEXT,
            choice TEXT,
            theme TEXT,
            question TEXT,
            meaning_other TEXT
        )""", ()
    )


async def replace_synonyms(text):
    words = text.lower().split()
    for i, word in enumerate(words):
        for key, synonyms_list in CARDS_NAME_SYNONYMS.items():
            if word in synonyms_list:
                words[i] = key
    name = " ".join(words)
    text = text.lower()
    for i in enumerate(text):
        for key, synonyms_list in CARDS_NAME_SYNONYMS.items():
            if text in synonyms_list:
                name = key
    return name


async def generate_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text = "Сохранить", callback_data = f"chat_meaning_save_{user_id}")
    builder.button(text = "Ситуация", callback_data = f"chat_meaning_savesituation_{user_id}")
    builder.button(text = "Варн", callback_data = f"chat_meaning_warn_{user_id}")
    builder.button(text = "Удалить", callback_data = f"chat_meaning_delete_{user_id}")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard = True)


@router.callback_query(F.data.startswith('chat_meaning_'))
async def meaning_cb(call: CallbackQuery, bot: Bot):
    await call.answer()
    chat_member = await bot.get_chat_member(chat_id = CHAT_ID, user_id = call.from_user.id)
    if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        call_parts = call.data.split('_')
        call_type = call_parts[2]
        user_id = call_parts[3]

        text = call.message.reply_to_message.text
        if text is None:
            text = call.message.reply_to_message.caption

        if call_type == "warn":
            text_warn = f"<a href='tg://user?id={user_id}'>Вам</a>"
            result = await execute_select(f"SELECT warns FROM users_chat WHERE user_id = {user_id}")

            if result is None:
                await execute_query(f"INSERT INTO users_chat(warns, user_id) VALUES(1, {user_id})", ())
                await bot.send_message(
                    chat_id = call.message.chat.id,
                    text = f"{text_warn} вынесли варн, перепишите трактовку по всем правилам в закрепленном сообщении",
                    reply_to_message_id = call.message.reply_to_message.message_id
                )
            else:
                warns = result[0] + 1
                if warns < 3:
                    await execute_query(f"UPDATE users_chat SET warns = {warns} WHERE user_id = {user_id}", ())
                    await bot.send_message(
                        chat_id = call.message.chat.id,
                        text = f"{text_warn} вынесли варн, перепишите трактовку по всем правилам в закрепленном сообщении",
                        reply_to_message_id = call.message.reply_to_message.message_id
                    )
                elif warns == 3:
                    await execute_query("DELETE FROM users_chat WHERE warns = 2", ())
                    await bot.ban_chat_member(chat_id = call.message.chat.id, user_id = int(user_id))
                    await call.answer("Пока, дружок.")

        elif call_type == "save":
            choice = text.split("#")[1]
            theme = "".join(text.split("#")[2]).split(" ")[0]

            elements = []
            text = text.replace("\n\n", "\n")
            lines = text.strip().split('\n')[1:]

            for line in lines:
                keyword, description = line.split(':', 1)
                elements.append((keyword.strip(), description.strip()))

            cards = []
            meaning = []
            situation = ""
            question = ""

            for element in elements:
                keyword = element[0].lower()
                keyword = await replace_synonyms(keyword)
                if keyword in CARDS:
                    cards.append(keyword + ".")
                    meaning.append(element[1] + ".")
                elif keyword == "ситуация":
                    situation = element[1]
                elif keyword == "общая трактовка":
                    meaning.append(element[1] + ".")
                elif keyword == "вопрос":
                    question = element[1]

            await execute_query(
                "INSERT INTO meaning_chat (cards, situation, meaningCards, choice, theme, question) VALUES (%s, %s, %s, %s, %s, %s)",
                (" ".join(cards), situation, " ".join(meaning), choice, theme, question)
            )

            result = await execute_select("SELECT num FROM meaning_chat ORDER BY num DESC LIMIT 1")
            num = result[0]

            await bot.edit_message_text(
                chat_id = call.message.chat.id,
                message_id = call.message.message_id,
                text = f'Сохранено. Номер трактовки — {num}.'
            )

        elif call_type == "savesituation":
            choice = text.split("#")[1]
            theme = "".join(text.split("#")[2]).split(" ")[0]

            elements = []
            text = text.replace("\n\n", "\n")
            lines = text.strip().split('\n')[1:]

            for line in lines:
                keyword, description = line.split(':', 1)
                elements.append((keyword.strip(), description.strip()))

            cards = []
            situation = ""
            question = ""

            for element in elements:
                keyword = element[0].lower()
                keyword = await replace_synonyms(keyword)
                if keyword in CARDS:
                    cards.append(keyword + ".")
                elif keyword == "ситуация":
                    situation = element[1]
                elif keyword == "вопрос":
                    question = element[1]

            await execute_query(
                "INSERT INTO meaning_chat (cards, situation, choice, theme, question) VALUES (%s, %s, %s, %s, %s)",
                (" ".join(cards), situation, choice, theme, question)
            )

            result = await execute_select("SELECT num FROM meaning_chat ORDER BY num DESC LIMIT 1")
            num = result[0]

            await bot.edit_message_text(
                chat_id = call.message.chat.id,
                message_id = call.message.message_id,
                text = f'Сохранено. Номер ситуации — {num}.'
            )

        elif call_type == "delete":
            await bot.delete_message(
                chat_id = call.message.chat.id,
                message_id = call.message.message_id
            )
            await bot.delete_message(
                chat_id = call.message.chat.id,
                message_id = call.message.reply_to_message.message_id
            )


async def check_text(message: Message, bot: Bot):
    text = message.text
    if text is None:
        text = message.caption

    pattern = re.compile(r'^#(\w+)\s#(\w+)')
    words = ['ситуация', 'общая трактовка', 'вопрос']

    if re.search(pattern, text):
        if all(word.lower() in text.lower() for word in words):
            keyboard = await generate_keyboard(message.reply_to_message.from_user.id)
            await message.reply(
                text = 'Жди помощи! Кнопки для администрации: ',
                reply_markup = keyboard
            )
        else:
            reply_message = await message.reply(
                'Напиши трактовку по заданному шаблону. Твое сообщение удалится через две минуты,'
                ' успей его скопировать и отправить новое по шаблону, НЕ РЕДАКТИРУЙ САМО СООБЩЕНИЕ.'
            )
            await asyncio.sleep(120)
            await bot.delete_message(chat_id = message.chat.id, message_id = message.message_id)


@router.message(F.chat.id == CHAT_ID, F.text.regexp(r'^!с\s'))
async def save_meaning_others(message: Message, bot: Bot):
    try:
        if message.reply_to_message:
            num = message.text.split(' ')[1]
            meaning = message.reply_to_message.text

            result = await execute_select(f"SELECT meaning_other FROM meaning_chat WHERE num = {num}")
            check = result[0] if result else None

            if check is not None:
                meaning = f"{check}\n{meaning}"

            await execute_query(
                "UPDATE meaning_chat SET meaning_other = %s WHERE num = %s",
                (meaning, num)
            )

            await message.reply('Cохранено!')
        else:
            await message.reply('Надо писать ответом на сообщение!')
    except Exception as e:
        await message.reply(f'Что-то пошло не так :( {str(e)}')


@router.message(F.chat.id == CHAT_ID, F.text.in_(['+', "согл", "согласен", "согласна"]))
async def get_reputation(message: Message, bot: Bot):
    if message.reply_to_message and not message.reply_to_message.is_topic_message:
        if message.reply_to_message.from_user.id != message.from_user.id:
            user_id = message.reply_to_message.from_user.id

            result = await execute_select(f"SELECT rep FROM users_chat WHERE user_id = {user_id}")
            rep = result[0] if result else None

            if rep is not None:
                rep = rep + 1
            else:
                result = await execute_select(f"SELECT user_id FROM users_chat WHERE user_id = {user_id}")
                if not result:
                    await execute_query(
                        "INSERT INTO users_chat (user_id) VALUES (%s)",
                        (user_id,)
                    )
                rep = 1

            await execute_query(
                "UPDATE users_chat SET rep = %s WHERE user_id = %s",
                (rep, user_id)
            )

            await bot.send_message(
                chat_id = message.chat.id,
                text = f'Вам выразили респект. Ваша репутация: {rep}',
                reply_to_message_id = message.reply_to_message.message_id
            )


@router.message(F.chat.id == CHAT_ID, F.content_type.in_(['new_chat_members', 'left_chat_member']))
async def delete_system_messages(message: Message):
    await message.delete()


@router.message(F.new_chat_members, F.chat.id == CHAT_ID)
async def new_members_handler(message: Message, bot: Bot):
    chat_id = message.chat.id
    new_member = message.new_chat_members[0].first_name
    user_id = message.new_chat_members[0].id

    try:
        if user_id == bot.id:
            await bot.send_message(
                chat_id = message.chat.id,
                text = "Приветствую. В статье вы сможете ознакомиться с правилами и инструкциями.",
                reply_markup = InlineKeyboardBuilder().button(
                    text = "Правила",
                    url = "https://telegra.ph/Lesnoj-Duh-Li-10-10"
                ).as_markup()
            )
        else:
            result = await execute_select(f"SELECT rules FROM chats WHERE chat_id = {chat_id}")
            rules = result[0] if result else None

            if rules:
                await bot.send_message(
                    chat_id = message.chat.id,
                    text = f"Добро пожаловать, <b>{new_member}.</b>\n\n{rules}",
                    parse_mode = "HTML"
                )
            else:
                await bot.send_message(
                    chat_id = message.chat.id,
                    text = f"Добро пожаловать, <b>{new_member}.</b>",
                    parse_mode = "HTML"
                )
    except Exception:
        await bot.send_message(
            chat_id = message.chat.id,
            text = f"Добро пожаловать, <b>{new_member}.</b>",
            parse_mode = "HTML"
        )


@router.message(F.text.lower() == "правила", F.chat.id == CHAT_ID)
async def set_rules(message: Message, bot: Bot):
    chat_id = message.chat.id
    try:
        result = await execute_select(f"SELECT rules FROM chats WHERE chat_id = {chat_id}")
        rules = result[0] if result else None

        if rules:
            await bot.send_message(chat_id = chat_id, text = rules)
        else:
            await bot.send_message(chat_id = chat_id, text = "У вас нет правил, позорники!")
    except Exception:
        await bot.send_message(chat_id = chat_id, text = "У вас нет правил, позорники!")


@router.message(F.chat.id == CHAT_ID)
async def process_message(message: Message, bot: Bot):
    text = message.text or message.caption
    if text:
        pattern = re.compile(r'^#(\w+)\s#(\w+)')
        if re.search(pattern, text) and message.reply_to_message:
            await check_text(message, bot)
