from aiogram import Bot, Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InputMediaDocument
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

from database import execute_select_all, execute_select, execute_query
from openai import AsyncOpenAI

from filters.baseFilters import IsReply, IsAdmin
from filters.subscriptions import SubscriptionLevel
from functions.gpt.requests import get_gpt_response
from middlewares.statsUser import use_user_statistics

BOOK_CHANNEL_ID = -1001607817353
client = AsyncOpenAI(api_key = os.environ.get("OPENAI_API_KEY"))

router = Router()


class SaveBooks(StatesGroup):
    save = State()


async def create_library_table():
    query = """
    CREATE TABLE IF NOT EXISTS library (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        keywords TEXT[],
        book_id VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    await execute_query(query, ())


async def analyze_book(file_name, file_extension):
    prompt = f"""
        Проанализируй книгу с названием "{file_name} и найди информации про нее в интернете".
        Создай:
        1. Краткое описание книги (2-3 предложения)
        2. Список из 3-5 ключевых тегов (без символа #)
        
        Подсказки: МБК значит руководство по таро, если в названии книги присуствует МБК и
        название колоды, значит напиши просто, что это руководство по той колоде.

        Формат ответа:
        Описание: [твое описание]
        Теги: [тег1, тег2, тег3]
        """

    messages = [
        {"role": "system", "content": "Ты - помощник, который анализирует книги и создает их описания и теги."},
        {"role": "user", "content": prompt}
    ]

    result = await get_gpt_response(messages)

    description_part = result.split("Описание:")[1].split("Теги:")[0].strip()
    tags_part = result.split("Теги:")[1].strip()
    tags = [tag.strip() for tag in tags_part.split(',')]

    return description_part, tags


@router.message(IsAdmin(), F.text.startswith("+книга"))
async def get_save_book(message: Message, state: FSMContext):
    await message.reply("Пришлите книгу, я автоматически создам описание и теги.")
    await state.set_state(SaveBooks.save)


@router.message(StateFilter(SaveBooks.save), F.document)
async def save_book(message: Message, state: FSMContext, bot: Bot):
    await message.reply("Анализирую книгу...")
    await create_library_table()

    if not message.document:
        await message.reply("Пожалуйста, отправьте документ (книгу).")
        return

    document = message.document
    file_name = document.file_name
    file_extension = file_name.split('.')[-1] if '.' in file_name else ""
    file_name_without_ext = '.'.join(file_name.split('.')[:-1]) if '.' in file_name else file_name

    description, tags = await analyze_book(file_name_without_ext, file_extension)

    keywords = tags

    msg = await bot.send_document(
        BOOK_CHANNEL_ID,
        document = document.file_id,
        caption = f"{description}\n\n#{' #'.join(tags)}"
    )

    file_id = msg.document.file_id

    await execute_query(
        "INSERT INTO library (title, description, keywords, book_id) VALUES ($1, $2, $3, $4)",
        (file_name_without_ext, description, keywords, file_id)
    )

    await message.reply(f"Книга сохранена!\n\nОписание: {description}\n\nТеги: #{' #'.join(tags)}")
    await state.clear()


@router.message(F.text.lower().startswith("книга"), SubscriptionLevel(1))
@use_user_statistics
async def find_books(message: Message, bot: Bot):
    if message.chat.type == "private":
        if len(message.text.split(' ')) == 1:
            builder = InlineKeyboardBuilder()
            builder.button(text = "Случайный выбор", callback_data = "show_random_book")

            examples = await execute_select("SELECT keywords FROM library GROUP BY keywords ORDER BY RANDOM() LIMIT 1")
            examples_str = examples[0].replace(',', ', ').replace('{', '').replace('}',
                                                                                   '') if examples else "фантастика"

            await message.reply(
                f'Выберите тематику запроса. К примеру: книга {examples_str}, \n\n Больше книг тут - @forestlibraryspirit',
                reply_markup = builder.as_markup(resize_keyboard = True)
            )
        else:
            keyword = message.text.split(' ')[1]

            books = await execute_select_all(
                "SELECT title, description, book_id FROM library WHERE EXISTS (SELECT 1 FROM unnest(keywords) keyword WHERE keyword ILIKE $1)",
                (f"%{keyword}%",)
            )

            if not books:
                await message.reply(f'Прости, ничего не найдено по запросу: {keyword}.')
            else:
                builder = InlineKeyboardBuilder()
                builder.button(text = "Искать книги", callback_data = f"show_book_0")

                current_book = books[0]
                title = current_book[0]
                description = current_book[1]
                book_id = current_book[2]
                book_message = f"<b>{title}:</b>\n\n{description}"

                await bot.send_document(
                    chat_id = message.chat.id,
                    caption = book_message,
                    document = book_id,
                    reply_markup = builder.as_markup(),
                    reply_to_message_id = message.message_id
                )


@router.callback_query(IsReply(), F.data.startswith('show_book'))
async def process_callback_show_book(call: CallbackQuery, bot: Bot):
    await call.answer()

    index = int(call.data.split('_')[2])
    keyword = call.message.reply_to_message.text.split(' ')[1]

    books = await execute_select_all(
        "SELECT title, description, book_id FROM library WHERE EXISTS (SELECT 1 FROM unnest(keywords) keyword WHERE keyword ILIKE $1)",
        (f"%{keyword}%",)
    )

    current_book = books[index]
    title = current_book[0]
    description = current_book[1]
    book_id = current_book[2]
    book_message = f"<b>{title}:</b>\n\n{description}"

    builder = InlineKeyboardBuilder()

    if len(books) == 1:
        pass
    elif index == 0:
        builder.button(text = "<--", callback_data = f"show_book_{len(books) - 1}")
        builder.button(text = "-->", callback_data = f"show_book_{index + 1}")
    elif index == len(books) - 1:
        builder.button(text = "<--", callback_data = f"show_book_{index - 1}")
        builder.button(text = "-->", callback_data = f"show_book_0")
    else:
        builder.button(text = "<--", callback_data = f"show_book_{index - 1}")
        builder.button(text = "-->", callback_data = f"show_book_{index + 1}")

    builder.adjust(2)

    media = InputMediaDocument(media = book_id, caption = book_message)

    await bot.edit_message_media(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        media = media,
        reply_markup = builder.as_markup()
    )


@router.callback_query(IsReply(), F.data == "show_random_book")
async def process_callback_show_random_book(call: CallbackQuery, bot: Bot):
    await call.answer()

    current_book = await execute_select_all(
        "SELECT title, description, book_id FROM library ORDER BY RANDOM() LIMIT 1")

    if current_book:
        current_book = current_book[0]
        title = current_book[0]
        description = current_book[1]
        book_id = current_book[2]
        book_message = f"<b>{title}:</b>\n\n{description}"

        await bot.send_document(
            chat_id = call.message.chat.id,
            caption = book_message,
            document = book_id,
            reply_to_message_id = call.message.reply_to_message.message_id
        )
