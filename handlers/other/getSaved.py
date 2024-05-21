from aiogram import types
from main import dp, bot
from aiogram.dispatcher.filters.state import State, StatesGroup


@dp.message_handler(lambda message: message.text.lower() == "моя матрица")
async def get_matrica(message: types.Message):
    try:
        user_id = message.from_user.id
        cursor.execute("select matrica from users where user_id = {}".format(user_id))
        file = cursor.fetchone()[0]
        await bot.send_photo(message.chat.id, photo = file, reply_to_message_id = message.message_id)
    except:
        await message.reply("У меня этого нет.")
        pass


class Save(StatesGroup):
    matrica = State()
    natalka = State()


@dp.message_handler(lambda message: message.text.lower() == "сохранить матрицу")
async def get_save_matrica(message: types.Message):
    await message.reply("Отправьте изображение своей матрицы на хранение, чтобы я мог ее скинуть вам в любой момент.")
    await Save.matrica.set()


@dp.message_handler(content_types = ['photo'], state = Save.matrica)
async def save_matrica(message: types.Message, state="*"):
    try:
        user_id = message.from_user.id
        file = message.photo[-1].file_id
        cursor.execute("UPDATE users SET matrica = '{}' where user_id = {};".format(file, user_id))
        await message.reply("Сделано!")
        db.commit()
    except:
        await message.reply("Не нервируй меня.")
    await state.finish()


@dp.message_handler(lambda message: message.text.lower() == "моя наталка")
async def get_natalka(message: types.Message):
    try:
        user_id = message.from_user.id
        cursor.execute("select natalka from users where user_id = {}".format(user_id))
        file = cursor.fetchone()[0]
        await bot.send_photo(message.chat.id, photo = file, reply_to_message_id = message.message_id)
    except:
        await message.reply("У меня этого нет.")
        pass


@dp.message_handler(lambda message: message.text.lower() == "сохранить наталку")
async def get_save_natalka(message: types.Message):
    await message.reply(
        "Отправьте изображение своей натальной карты на хранение, чтобы я мог ее скинуть вам в любой момент.")
    await Save.natalka.set()


@dp.message_handler(content_types = ['photo'], state = Save.natalka)
async def save_natalka(message: types.Message, state="*"):
    try:
        user_id = message.from_user.id
        file = message.photo[-1].file_id
        try:
            cursor.execute("UPDATE users SET natalka = '{}' where user_id = {};".format(file, user_id))
            await message.reply("Сделано!")
        except:
            cursor.execute("INSERT into users(user_id) VALUES ({})".format(user_id))
            cursor.execute("UPDATE users SET natalka = '{}' where user_id = {};".format(file, user_id))
            await message.reply("Сделано!")
    except:
        await message.reply("Не нервируй меня.")
    db.commit()
    await state.finish()
