import random
from database import execute_select


async def practice_quiz_post(bot, channel_id):
    numbers = random.sample(range(0, 74), 3)
    for num in numbers:
        card = await execute_select("select practice.name from practice where number = {}", (num,))

        correct_answer = await execute_select("select quiz_02 from practice where number = {}", (num,))

        false = random.sample(range(0, 74), 4)
        if num in false:
            false = random.sample(range(0, 74), 4)

        answers = []
        for el in false:
            false_answer = await execute_select("select quiz_02 from practice where number = {}", (el,))
            answers.append(false_answer)
        answers.append(correct_answer)
        random.shuffle(answers)

        c = await check_correct_answer(answers, correct_answer)

        await bot.send_poll(channel_id, f'Какое значение может быть у карты {card}?',
                            [f'{answers[0]}', f'{answers[1]}', f'{answers[2]}', f'{answers[3]}', f'{answers[4]}'],
                            type = 'quiz', correct_option_id = c)


async def check_correct_answer(answers, correct_answer):
    x = 0
    for el in answers:
        x = x + 1
        if el == correct_answer:
            c = x - 1
            return c
