from bot import dp, cursor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram import types


class Form(StatesGroup):
    name = State()
    city = State()
    photo = State()
    interests = State()


@dp.message_handler(lambda message: message.text.lower().startswith("!анкета"))
async def form_start(message: types.Message):
    await Form.name.set()
    await message.reply("Введите ваше имя.")


@dp.message_handler(state = Form.name)
async def process_age(message: types.Message, state: FSMContext):
    name = message.text

    await state.update_data(name = name)

    await Form.city.set()
    await message.reply("Введите ваш город.")


@dp.message_handler(state = Form.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city = message.text)

    await Form.photo.set()
    await message.reply("Отравьте свою фотографию. (ну или не свою). Это обязательно!")


@dp.message_handler(content_types = ['photo'], state = Form.photo)
async def process_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo = message.photo[-1].file_id)

    await Form.interests.set()
    await message.reply("Напишите что-то о себе. К примеру, эзотерически интересы, чем увлекаетесь и так далее.")


@dp.message_handler(state = Form.interests)
async def process_interests(message: types.Message, state: FSMContext):
    await state.update_data(interests = message.text)

    user_data = await state.get_data()

    cursor.execute(
        "INSERT INTO users (username, name, city, interest, photo) VALUES (%s, %s, %s, %s)",
        (message.from_user.username, user_data["name"], user_data["city"], user_data["interests"], user_data["photo"])
    )
    await state.finish()
    await message.reply("Ваша анкета была создана, спасибо!")


@dp.message_handler(lambda message: message.text.lower().startswith("!поиск"))
async def cmd_show(message: types.Message):
    cursor.execute(
        "SELECT city FROM users WHERE username = %s",
        (message.from_user.username,)
    )
    result = cursor.fetchone()
    if not result:
        await message.reply("Вы не заполнили анкету.")
        return
    user_city = result[0]

    cursor.execute(
        "SELECT username, name, interest FROM users WHERE city = %s AND username != %s",
        (user_city, message.from_user.username)
    )
    results = cursor.fetchall()

    if not results:
        await message.reply("Никого из твоего города пока что нет :(")
    else:
        for result in results:
            form = f"{result[0]}\n\n {result[1]}\n\n: {result[2]}"
            await message.answer(form)


@dp.message_handler(lambda message: message.text.lower().startswith("!удалить анкету"))
async def delete_form(message: types.Message):
    cursor.execute(
        "DELETE FROM users WHERE user_id = %s",
        (message.from_user.id,)
    )