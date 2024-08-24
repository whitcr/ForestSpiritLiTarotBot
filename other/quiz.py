from database import execute_select, execute_query
from main import cursor, dp, db, bot
from aiogram import types
from aiogram.dispatcher import FSMContext
import random
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_button = InlineKeyboardButton(text = "Начать викторину", callback_data = "start_quiz")
start_quiz_keyboard = InlineKeyboardMarkup(resize_keyboard = True).add(start_button)


@dp.message_handler(lambda message: message.text.lower().startswith("вик"))
async def start(message: types.Message):
    user = f"<a href = 'tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>"
    await message.answer(f'<b>Привет {user}, рада приветствовать тебя на моей праздничной викторине!</b> '
                         f'\n\nТак как у моего канала день рождения — сегодня будет марафон скидок и подарков 😻\n'
                         f'Твоя задача - правильно отвечать на вопросы, и чем больше правильных ответов — тем интереснее приз🙀\n\n'
                         f'<b>Когда дойдешь до последнего вопроса — твой приз уже будет ожидать тебя </b>😎')
    await message.answer(
        f'<b>Условия Викторины:</b>'
        f'\n\nВаша задача просто правильно отвечать на вопросы. На один вопрос отводится не более 5 минут. Если время пропущено — викторина прекращается :)'
        f'\n\n<b>Внимание! Викторину можно пройти один раз! Поэтому если начали — придется закончить сразу, чтобы получить свой приз :)</b>'
        f'\n\nНу что, погнали?', reply_markup = start_quiz_keyboard)


from contextlib import suppress


async def timeout(question, user_id, sleep_time: int = 0):
    try:
        await asyncio.sleep(sleep_time)

        num = await execute_select("select question from quiz_holion where user_id = {}", (user_id,))

        timeout = await execute_select("select timeout from quiz_holion where user_id = {}", (user_id,))

        if timeout == 1 and question == num:
            await bot.send_message(user_id,
                                   f'К сожалению, ты пропустил время ответа на вопрос и выбываешь из викторины. '
                                   f'Было приятно тебя тут увидеть, в следующий раз ты сможешь дойти до конца, а пока что — До новых встреч♥️')
        else:
            pass
    except:
        pass


# @dp.message_handler(lambda message: message.text.lower() == "тест")
# async def get_test_quiz(message: types.Message, state="*"):

@dp.callback_query_handler(lambda call: call.data == 'start_quiz')
async def get_test_quiz(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if call.message.chat.type == 'private':
        try:
            try:
                check = await execute_select("select user_id from quiz_holion where user_id = {}",
                                             (call.message.chat.id,))

            except:
                await execute_query("insert into quiz_holion(user_id, question) values ({},{})",
                                    (call.message.chat.id, 1))

            try:
                check = await execute_select("select joint from quiz_holion where user_id = {}",
                                             (call.message.chat.id,))

                if check == None:
                    check = 2
            except:
                check = 2

            if check == 90:
                await bot.send_message(call.message.chat.id,
                                       'Ах ты хитрая змейка! Всёёё, больше нельзя 😜 ')
            else:
                await test_quiz(call.message.chat.id, state)
                await execute_query("UPDATE quiz_holion SET joint = {} where user_id = {};", (0, call.message.chat.id))

        except:
            await bot.send_message(call.message.chat.id,
                                   "Что-то пошло не так, сообщи администратору")
    else:
        await bot.send_message(call.message.chat.id,
                               "Викторина работает только в Личных Сообщениях.")


async def test_quiz(user_id, state: FSMContext):
    try:
        await execute_query("UPDATE quiz_holion SET timeout = {} where user_id = {};", (1, user_id))

        num = await execute_select("select question from quiz_holion where user_id = {}", (user_id,))

        new_num = num + 1

        question = await execute_select("select question from quiz_holion_text where num = {}", (num,))
        correct_answer = await execute_select("select option_0 from quiz_holion_text where num = {}", (num,))
        option_1 = await execute_select("select option_1 from quiz_holion_text where num = {}", (num,))
        option_2 = await execute_select("select option_2 from quiz_holion_text where num = {}", (num,))
        option_3 = await execute_select("select option_3 from quiz_holion_text where num = {}", (num,))

        # ignore = [num]
        # ran = [ind for ind in range(7) if ind not in ignore]

        answers = []
        answers.append(correct_answer)
        answers.append(option_1)
        answers.append(option_2)
        answers.append(option_3)
        random.shuffle(answers)

        # false = random.sample(ran, 4)

        # for el in false:
        #     cursor.execute("select practice.handlers from practice where number = {}",(el))
        #     false_answer = cursor.fetchone()[0]
        #     answers.append(false_answer)

        c = await check_correct_answer(answers, correct_answer)

        # try:
        #     cursor.execute("select image from quiz_holion_text where number = {}",(num))
        #     image = cursor.fetchone()[0]
        #     await bot.send_photo(user_id, photo=image)
        # except:
        #     pass

        # global this_quiz
        poll = await bot.send_poll(user_id, f'{question}',
                                   [f'{answers[0]}', f'{answers[1]}', f'{answers[2]}', f'{answers[3]}'],
                                   type = 'handlers', correct_option_id = c, is_anonymous = False, open_period = 300)

        await state.update_data(poll = poll)
        asyncio.create_task(timeout(num, user_id, 320))
    except:
        pass


async def check_correct_answer(answers, correct_answer):
    x = 0
    for el in answers:
        x = x + 1
        if el == correct_answer:
            c = x - 1
            return c


@dp.poll_answer_handler()
async def handle_poll_answer(quiz_answer: types.PollAnswer):
    state = dp.current_state(chat = quiz_answer.user.id, user = quiz_answer.user.id)
    # poll = state.get_state().poll
    # poll = state.get_state().poll
    poll = await state.get_data()
    poll = poll.get("poll")
    poll = poll.poll

    await execute_query("UPDATE quiz_holion SET timeout = {} where user_id = {};", (0, quiz_answer.user.id))

    num = await execute_select("select question from quiz_holion where user_id = {}", (quiz_answer.user.id,))

    new_num = num + 1
    # poll = await state.get_data()["poll"]
    if poll.correct_option_id == quiz_answer.option_ids[0]:
        text = await execute_select("select r_ans from quiz_holion_text where num = {}", (num,))

        await bot.send_message(quiz_answer.user.id, text = f'{text}')

        try:
            counter = await execute_select("select counter from quiz_holion where user_id = {}", (quiz_answer.user.id,))

            counter = 1 + counter
        except:
            counter = 1

        await execute_query("UPDATE quiz_holion SET counter = {} where user_id = {};", (counter, quiz_answer.user.id,))

    else:
        text = await execute_select("select w_ans from quiz_holion_text where num = {}", (num,))

        await bot.send_message(quiz_answer.user.id, text = f'{text}')

        try:
            counter = await execute_select("select counter from quiz_holion where user_id = {}", (quiz_answer.user.id,))

        except:
            counter = 1

    await execute_query(
        "UPDATE quiz_holion SET question = {} where user_id = {};", (new_num, quiz_answer.user.id))

    if new_num != 11:
        await test_quiz(quiz_answer.user.id, state)
    else:
        if counter <= 5:
            await bot.send_message(quiz_answer.user.id,
                                   f'<b> Твой результат: </b>'
                                   f'\n\n {counter} правильных ответов!'
                                   f'<b> Твой приз: </b>'
                                   f'\n\n 🙀 Скидка 50% на диагностику негатива или родовых каналов'
                                   f'\n\n<b>Я рада, что ты со мной </b>♥️')
        if counter == 6 or counter == 7 or counter == 8:
            await bot.send_message(quiz_answer.user.id,
                                   f'<b> Твой результат: </b>'
                                   f'\n\n {counter} правильных ответов!'
                                   f'<b> Твой приз: </b>'
                                   f'\n\n🙀 Скидка 50% на диагностику негатива или родовых каналов'
                                   f'\n🙀 Скидка 60% на любую лекцию из прайса'
                                   f'\n\n<b>Я рада, что ты со мной </b>♥️')
        if counter == 9:
            await bot.send_message(quiz_answer.user.id,
                                   f'<b> Твой результат: </b>'
                                   f'\n\n {counter} правильных ответов!'
                                   f'<b> Твой приз: </b>'
                                   f'\n\n🙀 Скидка 50% на диагностику негатива или родовых каналов'
                                   f'\n🙀 Скидка 60% на любую лекцию из прайса'
                                   f'\n🙀 Скидка 50% на ритуал чистки'
                                   f'\n\n<b>Я рада, что ты со мной </b>♥️')
        if counter == 10:
            await bot.send_message(quiz_answer.user.id,
                                   f'<b> Твой результат: </b>'
                                   f'\n\n {counter} правильных ответов!'
                                   f'<b> Твой приз: </b>'
                                   f'\n\n🙀 Скидка 50% на диагностику негатива или родовых каналов'
                                   f'\n🙀 Скидка 60% на любую лекцию из прайса'
                                   f'\n🙀 Скидка 50% на ритуал чистки'
                                   f'\n🙀 Лекция по чакрам в доступ на 1 мес'
                                   f'\n\n<b>Я рада, что ты со мной </b>♥️')
    # cursor.execute("UPDATE quiz_holion SET joint = {} where user_id = {};",(1, quiz_answer.user.id))
    # db.commit()

# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
#
# image_block_button = InlineKeyboardButton(text="Опрос с картинкой", callback_data="image_block")
# text_block_button = InlineKeyboardButton(text="Опрос", callback_data="text_block")
# create_keyboard =  InlineKeyboardMarkup(resize_keyboard=True).add(text_block_button, image_block_button)

# @dp.message_handler(lambda message: message.text.lower() == "создать")
# async def create_test_quiz(message: types.Message, state="*"):
#     await bot.send_message(message.from_user.id, 'Какой блок викторины хотите добавить?', reply_markup=create_keyboard)
#
# class Create(StatesGroup):
#     question = State()
#     answer = State()
#     option_02 = State()
#     option_03 = State()
#     option_04 = State()
#
#
# @dp.callback_query_handler(lambda call: call.data == 'text_block')
# async def image_block_cb(call: types.CallbackQuery):
#     await call.answer()
#     await call.message.answer(
#         f"Введите вопрос")
#     await Create.question.set()
#
# @dp.message_handler(state=Create.question)
# async def get_question(message: types.Message, state: FSMContext):
#     await state.update_data(question=message.text)
#     await message.answer("Введите верный ответ")
#     await Create.answer.set()
#
# @dp.message_handler(state=Create.answer)
# async def get_question(message: types.Message, state: FSMContext):
#     await state.update_data(answer=message.text)
#     await message.answer("Введите неверный ответ")
#     await Create.option_02.set()
#
# @dp.message_handler(state=Create.option_02)
# async def get_question(message: types.Message, state: FSMContext):
#     await state.update_data(option_02=message.text)
#     await message.answer("Введите неверный ответ")
#     await Create.option_03.set()
#
# @dp.message_handler(state=Create.option_03)
# async def get_question(message: types.Message, state: FSMContext):
#     await state.update_data(option_03=message.text)
#     await message.answer("Введите неверный ответ")
#     await Create.option_04.set()
#
# @dp.message_handler(state=Create.option_04)
# async def get_question(message: types.Message, state: FSMContext):
#     await state.update_data(option_04=message.text)
#     data = await state.get_data()
#     question = str(data['question'])
#     answer = str(data['answer'])
#     option_02 = str(data['option_02'])
#     option_03 = str(data['option_03'])
#     option_04 = str(data['option_04'])
