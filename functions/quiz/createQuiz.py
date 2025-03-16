from aiogram import Bot, types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, PollAnswer, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import json
import random
import logging
from config import load_config

from database import execute_query, execute_select, execute_select_all
from filters.baseFilters import IsAdmin

router = Router()
config = load_config()
logger_chat = config.tg_bot.logger_chat


async def init_db():
    await execute_query(
        "CREATE TABLE IF NOT EXISTS quiz_settings (id SERIAL PRIMARY KEY,is_active BOOLEAN DEFAULT TRUE,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        ())

    await execute_query('''
            CREATE TABLE IF NOT EXISTS quiz_participants (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                question_num INTEGER DEFAULT 1,
                correct_answers INTEGER DEFAULT 0,
                is_timeout BOOLEAN DEFAULT FALSE,
                is_completed BOOLEAN DEFAULT FALSE,
                current_correct_index INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''', ())

    # Проверяем наличие настроек, если нет - создаем
    settings = await execute_select_all('SELECT * FROM quiz_settings LIMIT 1')
    if not settings:
        await execute_query('INSERT INTO quiz_settings (is_active) VALUES (TRUE)')


def load_quiz_data():
    try:
        with open('functions/quiz/quiz.json', 'r', encoding = 'utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Quiz data file not found!")
        return None


start_button = InlineKeyboardButton(text = "Начать викторину", callback_data = "start_quiz")
start_quiz_keyboard = InlineKeyboardMarkup(inline_keyboard = [[start_button]])

admin_keyboard = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton(text = "Статистика участников")],
        [KeyboardButton(text = "Включить/Выключить викторину")],
        [KeyboardButton(text = "Экспорт результатов")]
    ],
    resize_keyboard = True
)


@router.message(F.text.lower().startswith("вик"))
async def start_command(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    await init_db()
    # Проверка активности викторины

    settings = await execute_select_all('SELECT * FROM quiz_settings ORDER BY id DESC LIMIT 1')
    if not settings[0] or not settings[0]['is_active']:
        await message.answer("Извините, викторина в данный момент не активна.")
        return

    user = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"

    await message.answer(
        f'<b>Привет {user}, рада приветствовать тебя на викторине!</b> '
        f'\n\nСегодня у нас интересные вопросы и подарки для победителей 😻\n'
        f'Твоя задача - правильно отвечать на вопросы, и чем больше правильных ответов — тем интереснее приз🙀\n\n'
        f'<b>Когда дойдешь до последнего вопроса — твой приз уже будет ожидать тебя</b> 😎'
    )

    await message.answer(
        f'<b>Условия Викторины:</b>'
        f'\n\nВаша задача просто правильно отвечать на вопросы. На один вопрос отводится не более 5 минут. '
        f'Если время пропущено — викторина прекращается :)'
        f'\n\n<b>Внимание! Викторину можно пройти один раз! Поэтому если начали — придется закончить сразу, '
        f'чтобы получить свой приз :)</b>'
        f'\n\nНу что, погнали?',
        reply_markup = start_quiz_keyboard
    )


async def timeout_task(bot, user_id: int, question_num: int, sleep_time: int = 300):
    try:
        await asyncio.sleep(sleep_time)

        # Проверяем, если пользователь все еще на том же вопросе
        user = await execute_select_all(
            'SELECT * FROM quiz_participants WHERE user_id = $1', (user_id,)
        )

        user = user[0]

        if user and user['question_num'] == question_num and not user['is_completed'] and not user['is_timeout']:
            # Обновляем статус в БД
            await execute_query(
                'UPDATE quiz_participants SET is_timeout = TRUE, is_completed = TRUE, completed_at = CURRENT_TIMESTAMP WHERE user_id = $1',
                (user_id,)
            )

            # Отправляем сообщение пользователю
            await bot.send_message(
                user_id,
                f'К сожалению, ты пропустил время ответа на вопрос и выбываешь из викторины. '
                f'Было приятно тебя тут увидеть, в следующий раз ты сможешь дойти до конца, а пока что — До новых встреч♥️'
            )

            # Логируем в чат администраторов
            await log_to_chat(bot,
                              f"Пользователь {user['full_name']} (ID: {user_id}) пропустил время ответа на вопрос {question_num}")
    except Exception as e:
        logging.error(f"Error in timeout task: {e}")


async def log_to_chat(bot, message: str):
    await bot.send_message(logger_chat, f"📝 {message}")


@router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id

    # Check if in private chat
    if callback.message.chat.type != 'private':
        await callback.message.answer("Викторина работает только в Личных Сообщениях.")
        return

    # Проверка активности викторины

    settings = await execute_select_all('SELECT * FROM quiz_settings ORDER BY id DESC LIMIT 1')
    settings = settings[0]
    if not settings or not settings['is_active']:
        await callback.message.answer("Извините, викторина в данный момент не активна.")
        return

    # Проверяем, проходил ли уже пользователь викторину
    user = await execute_select_all(
        'SELECT * FROM quiz_participants WHERE user_id = $1',
        (user_id,)
    )
    user = user[0] if user else None

    if user and user['is_completed']:
        await callback.message.answer('Ах ты хитрая змейка! Всёёё, больше нельзя 😜')
        return

    # Если пользователь уже начинал, но не закончил - сбрасываем прогресс
    if user:
        await execute_query(
            '''
            UPDATE quiz_participants 
            SET question_num = 1, correct_answers = 0, is_timeout = FALSE, 
                is_completed = FALSE, started_at = CURRENT_TIMESTAMP, completed_at = NULL 
            WHERE user_id = $1
            ''',
            (user_id,)
        )
    else:
        # Создаем нового участника
        await execute_query(
            '''
            INSERT INTO quiz_participants (user_id, username, full_name) 
            VALUES ($1, $2, $3)
            ''',
            (user_id, callback.from_user.username, callback.from_user.full_name)
        )

    # Логируем начало викторины
    await log_to_chat(bot, f"Пользователь {callback.from_user.full_name} (ID: {user_id}) начал викторину")

    # Start the quiz
    try:
        await send_question(user_id, state, bot)
    except Exception as e:
        logging.error(f"Error starting quiz: {e}")
        await callback.message.answer("Что-то пошло не так, попробуйте еще раз или сообщите администратору.")


async def send_question(user_id: int, state: FSMContext, bot):
    quiz_data = load_quiz_data()
    if not quiz_data:
        await bot.send_message(user_id, "Ошибка загрузки вопросов. Пожалуйста, сообщите администратору.")
        return

    # Получаем текущий номер вопроса из БД

    user = await execute_select_all(
        'SELECT * FROM quiz_participants WHERE user_id = $1',
        (user_id,)
    )
    user = user[0]

    if not user:
        logging.error(f"User {user_id} not found in database")
        await bot.send_message(user_id, "Произошла ошибка. Попробуйте начать викторину снова.")
        return

    question_num = user['question_num']

    # Check if we've reached the end of the quiz
    if question_num > len(quiz_data["questions"]):
        await end_quiz(user_id, bot)
        return

    # Get question data
    question_data = quiz_data["questions"][question_num - 1]
    question_text = question_data["question"]
    correct_answer = question_data["correct_answer"]
    incorrect_answers = question_data["incorrect_answers"]

    # Create answers list with all options
    answers = [correct_answer] + incorrect_answers
    random.shuffle(answers)  # Randomize answer order

    # Find the index of the correct answer
    correct_index = answers.index(correct_answer)

    # Сохраняем правильный индекс в БД
    await execute_query(
        'UPDATE quiz_participants SET current_correct_index = $1 WHERE user_id = $2',
        (correct_index, user_id)
    )

    # Отправляем вопрос
    poll = await bot.send_poll(
        user_id,
        question_text,
        answers,
        type = 'quiz',
        correct_option_id = correct_index,
        is_anonymous = False,
        open_period = 300  # 5 minutes
    )

    # Save poll ID in state
    await state.update_data(poll_id = poll.message_id)

    # Start timeout task
    asyncio.create_task(timeout_task(bot, user_id, question_num))


@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, state: FSMContext, bot: Bot):
    user_id = poll_answer.user.id

    # Проверяем существование пользователя в БД

    user = await execute_select_all(
        'SELECT * FROM quiz_participants WHERE user_id = $1',
        (user_id,)
    )
    user = user[0]

    if not user:
        logging.error(f"User {user_id} not found in database")
        return

    # Получаем номер вопроса и индекс правильного ответа
    question_num = user['question_num']
    correct_index = user['current_correct_index']

    # Отключаем таймаут, т.к. пользователь ответил
    await execute_query(
        'UPDATE quiz_participants SET is_timeout = FALSE WHERE user_id = $1',
        (user_id,)
    )

    # Получаем данные викторины
    quiz_data = load_quiz_data()
    if not quiz_data:
        logging.error("Failed to load quiz data")
        return

    # Получаем данные текущего вопроса
    question_data = quiz_data["questions"][question_num - 1]

    # Проверяем правильность ответа
    selected_option = poll_answer.option_ids[0]

    # Обновляем статистику в БД

    if selected_option == correct_index:
        # Правильный ответ
        await execute_query(
            'UPDATE quiz_participants SET correct_answers = correct_answers + 1 WHERE user_id = $1',
            (user_id,)
        )
        await bot.send_message(user_id, question_data["correct_text"])

        # Логируем правильный ответ
        await log_to_chat(bot,
                          f"Пользователь {user['full_name']} (ID: {user_id}) правильно ответил на вопрос {question_num}")
    else:
        # Неправильный ответ
        await bot.send_message(user_id, question_data["wrong_text"])

        # Логируем неправильный ответ
        await log_to_chat(bot,
                          f"Пользователь {user['full_name']} (ID: {user_id}) неправильно ответил на вопрос {question_num}")

    # Увеличиваем номер вопроса
    await execute_query(
        'UPDATE quiz_participants SET question_num = question_num + 1 WHERE user_id = $1',
        (user_id,)
    )

    # Отправляем следующий вопрос
    await send_question(user_id, state, bot)


async def end_quiz(user_id: int, bot):
    # Получаем данные пользователя
    user = await execute_select_all(
        'SELECT * FROM quiz_participants WHERE user_id = $1',
        (user_id,)
    )
    user = user[0]

    if not user:
        logging.error(f"User {user_id} not found in database")
        return

    # Отмечаем викторину как завершенную
    await execute_query(
        'UPDATE quiz_participants SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP WHERE user_id = $1',
        (user_id,)
    )

    correct_answers = user['correct_answers']

    # Получаем данные викторины
    quiz_data = load_quiz_data()
    if not quiz_data:
        logging.error("Failed to load quiz data")
        return

    # Находим соответствующий приз на основе количества правильных ответов
    prize = ""
    for prize_tier in quiz_data["prizes"]:
        min_correct = prize_tier["min_correct"]
        max_correct = prize_tier["max_correct"]

        if min_correct <= correct_answers <= max_correct:
            prize = prize_tier["prize_text"]
            break

    # Отправляем результаты
    await bot.send_message(
        user_id,
        f'<b>Твой результат:</b>'
        f'\n\n{correct_answers} правильных ответов!'
        f'\n<b>Твой приз:</b>'
        f'\n\n{prize}'
        f'\n\n<b>Спасибо за участие!</b> ♥️'
    )

    # Логируем завершение викторины
    await log_to_chat(
        bot,
        f"Пользователь {user['full_name']} (ID: {user_id}) завершил викторину с результатом: {correct_answers} правильных ответов. Приз: {prize}"
    )


@router.message(IsAdmin(), F.text == "!вик")
async def admin_command(message: types.Message):
    await message.answer("Добро пожаловать в админ-панель викторины!", reply_markup = admin_keyboard)


@router.message(F.text == "Статистика участников")
async def show_statistics(message: types.Message):
    user_id = message.from_user.id

    # Получаем общую статистику
    total_participants = await execute_select('SELECT COUNT(*) FROM quiz_participants')
    completed_participants = await execute_select('SELECT COUNT(*) FROM quiz_participants WHERE is_completed = TRUE')
    active_participants = await execute_select('SELECT COUNT(*) FROM quiz_participants WHERE is_completed = FALSE')

    # Получаем статистику по правильным ответам
    avg_correct = await execute_select(
        'SELECT AVG(correct_answers) FROM quiz_participants WHERE is_completed = TRUE')
    max_correct = await execute_select(
        'SELECT MAX(correct_answers) FROM quiz_participants WHERE is_completed = TRUE')

    # Получаем настройки викторины
    settings = await execute_select_all('SELECT * FROM quiz_settings ORDER BY id DESC LIMIT 1')
    settings = settings[0]
    quiz_status = "Активна" if settings and settings['is_active'] else "Отключена"

    # Формируем сообщение со статистикой
    stats_message = (
        f"📊 <b>Статистика викторины</b>\n\n"
        f"🔹 Статус викторины: <b>{quiz_status}</b>\n"
        f"🔹 Всего участников: <b>{total_participants}</b>\n"
        f"🔹 Завершили викторину: <b>{completed_participants}</b>\n"
        f"🔹 Активных участников: <b>{active_participants}</b>\n"
        f"🔹 Среднее количество правильных ответов: <b>{avg_correct:.1f}</b>\n"
        f"🔹 Максимальное количество правильных ответов: <b>{max_correct}</b>\n"
    )

    await message.answer(stats_message, parse_mode = "HTML")


@router.message(F.text == "Включить/Выключить викторину")
async def toggle_quiz(message: types.Message):
    user_id = message.from_user.id

    settings = await execute_select_all('SELECT * FROM quiz_settings ORDER BY id DESC LIMIT 1')
    settings = settings[0]
    current_status = settings and settings['is_active']

    # Создаем кнопки включения/выключения
    buttons = [
        [InlineKeyboardButton(text = "✅ Включить", callback_data = "quiz_enable")],
        [InlineKeyboardButton(text = "❌ Выключить", callback_data = "quiz_disable")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    status_text = "включена" if current_status else "выключена"
    await message.answer(
        f"Сейчас викторина <b>{status_text}</b>. Выберите действие:",
        reply_markup = keyboard,
        parse_mode = "HTML"
    )


@router.callback_query(F.data.startswith("quiz_"))
async def quiz_toggle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    action = callback.data.split("_")[1]

    if action == "enable":
        await execute_query(
            'UPDATE quiz_settings SET is_active = TRUE WHERE id = (SELECT MAX(id) FROM quiz_settings)')
        await callback.message.edit_text("✅ Викторина успешно включена!")
        await log_to_chat(callback.bot, f"Администратор (ID: {user_id}) включил викторину")
    elif action == "disable":
        await execute_query(
            'UPDATE quiz_settings SET is_active = FALSE WHERE id = (SELECT MAX(id) FROM quiz_settings)')
        await callback.message.edit_text("❌ Викторина успешно отключена!")
        await log_to_chat(callback.bot, f"Администратор (ID: {user_id}) отключил викторину")

    await callback.answer()


@router.message(F.text == "Экспорт результатов")
async def export_results(message: types.Message, bot: Bot):
    user_id = message.from_user.id

    # Создаем кнопки для выбора формата экспорта
    buttons = [
        [InlineKeyboardButton(text = "📄 Текстовый отчет", callback_data = "export_text")],
        [InlineKeyboardButton(text = "📊 Полный список участников", callback_data = "export_full")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)

    await message.answer(
        "Выберите формат экспорта результатов:",
        reply_markup = keyboard
    )


@router.callback_query(F.data.startswith("export_"))
async def export_callback(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    await callback.answer()
    export_type = callback.data.split("_")[1]

    if export_type == "text":
        # Формируем текстовую сводку
        total_participants = await execute_select('SELECT COUNT(*) FROM quiz_participants')
        completed_participants = await execute_select(
            'SELECT COUNT(*) FROM quiz_participants WHERE is_completed = TRUE')

        # Группировка по количеству правильных ответов
        results = await execute_select_all('''
                SELECT correct_answers, COUNT(*) as count 
                FROM quiz_participants 
                WHERE is_completed = TRUE 
                GROUP BY correct_answers 
                ORDER BY correct_answers DESC
            ''')

        report = (
            f"📊 <b>Отчет по викторине</b>\n\n"
            f"Всего участников: {total_participants}\n"
            f"Завершили викторину: {completed_participants}\n\n"
            f"<b>Распределение результатов:</b>\n"
        )

        for row in results:
            report += f"{row['correct_answers']} правильных ответов: {row['count']} участников\n"

        await callback.message.edit_text(report, parse_mode = "HTML")

    elif export_type == "full":
        # Полный список участников
        participants = await execute_select_all('''
                SELECT user_id, username, full_name, correct_answers, is_completed, is_timeout, 
                       started_at, completed_at
                FROM quiz_participants 
                ORDER BY correct_answers DESC, completed_at ASC
            ''')

        # Отправляем первую часть сообщения
        await callback.message.edit_text(
            f"📋 <b>Полный список участников викторины ({len(participants)})</b>\n\n"
            f"Список будет отправлен несколькими сообщениями...",
            parse_mode = "HTML"
        )

        # Делим список на части, чтобы не превысить лимит сообщения
        chunk_size = 10  # Количество участников в одном сообщении
        for i in range(0, len(participants), chunk_size):
            chunk = participants[i:i + chunk_size]

            report = ""
            for idx, p in enumerate(chunk, start = i + 1):
                status = "✅ Завершил" if p['is_completed'] and not p['is_timeout'] else "⏱ Тайм-аут" if p[
                    'is_timeout'] else "🔄 Активен"
                completed = p['completed_at'].strftime("%d.%m.%Y %H:%M") if p['completed_at'] else "—"

                report += (
                    f"{idx}. <b>{p['full_name']}</b> (@{p['username'] or '—'})\n"
                    f"   ID: {p['user_id']}, Баллы: {p['correct_answers']}\n"
                    f"   Статус: {status}\n"
                    f"   Начал: {p['started_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"   Завершил: {completed}\n\n"
                )

            await bot.send_message(user_id, report, parse_mode = "HTML")
            await asyncio.sleep(0.3)  # Небольшая задержка между сообщениями
