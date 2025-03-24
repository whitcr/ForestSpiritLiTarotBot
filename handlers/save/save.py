from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database import execute_select, execute_query
from filters.subscriptions import SubscriptionLevel

router = Router()


class Save(StatesGroup):
    matrica = State()
    natalka = State()


@router.message(F.text.lower() == "моя матрица", SubscriptionLevel(1))
async def get_matrica(message: Message, bot: Bot):
    user_id = message.from_user.id
    file = await execute_select("SELECT matrica FROM users WHERE user_id = $1", (user_id,))

    if file:
        await bot.send_photo(message.chat.id, photo = file, reply_to_message_id = message.message_id)
    else:
        await message.reply("У меня этого нет.")


@router.message(StateFilter(None), F.text.lower() == "сохранить матрицу", SubscriptionLevel(2))
async def get_save_matrica(message: Message, state: FSMContext):
    await message.reply("Отправьте изображение своей матрицы на хранение.")
    await state.set_state(Save.matrica)


@router.message(Save.matrica)
async def save_matrica(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        file = message.photo[-1].file_id

        try:
            await execute_query("UPDATE users SET matrica = $1 WHERE user_id = $2;", (file, user_id))
            await message.reply("Сделано!")
        except Exception as e:
            await message.reply("Ошибка при сохранении матрицы.")

    except Exception as e:
        await message.reply("Ошибка при сохранении матрицы. Вы точно отправили фото?")

    await state.clear()


@router.message(F.text.lower() == "моя наталка", SubscriptionLevel(2))
async def get_natalka(message: Message, bot: Bot):
    user_id = message.from_user.id
    file = await execute_select("SELECT natalka FROM users WHERE user_id = $1", (user_id,))

    if file:
        await bot.send_photo(message.chat.id, photo = file, reply_to_message_id = message.message_id)
    else:
        await message.reply("У меня этого нет.")


@router.message(StateFilter(None), F.text.lower() == "сохранить наталку", SubscriptionLevel(2))
async def get_save_natalka(message: Message, state: FSMContext):
    await message.reply("Отправьте изображение своей натальной карты на хранение.")
    await state.set_state(Save.natalka)


@router.message(Save.natalka)
async def save_natalka(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        file = message.photo[-1].file_id

        try:
            updated = await execute_query("UPDATE users SET natalka = $1 WHERE user_id = $2;", (file, user_id))
            if not updated:
                await execute_query("INSERT INTO users (user_id, natalka) VALUES ($1, $2);", (user_id, file))
            await message.reply("Сделано!")
        except Exception as e:
            await message.reply("Ошибка при сохранении наталки.")
            print(e)

    except Exception as e:
        await message.reply("Ошибка при сохранении матрицы. Вы точно отправили фото?")

    await state.clear()
