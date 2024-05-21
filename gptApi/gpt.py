from aiogram import types, F, Router
from aiogram.utils import markdown
import openai
import asyncio
from random import randint

from main import ADMIN_ID
from config import CHANNEL_ID
from database import execute_select
from main import bot

router = Router()


def get_gpt_response(messages):
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages
    )
    return response.choices[0].message['content']


@router.message(F.from_user.id == ADMIN_ID)
async def chat(message: types.Message):
    user_input = message.text.replace("/chat", "").strip()

    if not user_input:
        return await message.reply("Пожалуйста, введите ваш вопрос после команды /chat")

    messages = [
        {'role': 'system',
         'content': 'Ты помощник в трактовках карт таро, ты знаешь все трактовки карт таро по Уэйту и умеешь объяснять их. '
                    'Твой стиль прост и повседневен, но не лишен глубокомыслия. Ты умеешь приводить повседневные примеры из '
                    'жизни в трактовках карт.'},
        {'role': 'user', 'content': user_input}
    ]

    message_text = await asyncio.to_thread(get_gpt_response, messages)
    await message.reply(markdown.text(message_text))


async def get_text_energy_day(cards):
    text = f"Напиши краткую трактовку карт {', '.join(cards)} на вопрос какие энергии преследовали нас сегодня, также сделай "\
           f"краткую общую трактовку. Стиль должен быть обыденным и легким. Трактовка не должна быть ОЧЕВИДНОЙ И ОБЫЧНОЙ,"\
           f" надо привести обыденные примеры, также можно использовать юмор, чтобы любой мог понять то, как проигрались значения "\
           f"этих карт в этот день. Начни сразу с трактовок карт без приветствия. Твой текст не должен быть длинее, чем 1200 символов."

    messages = [
        {'role': 'system',
         'content': 'Ты помощник в трактовках карт таро, ты знаешь все трактовки карт таро по Уэйту и умеешь объяснять их. '
                    'Твой стиль прост и повседневен, но не лишен глубокомыслия. Ты умеешь приводить повседневные примеры из'
                    ' жизни в трактовках карт.'},
        {'role': 'user', 'content': text}
    ]

    message = await asyncio.to_thread(get_gpt_response, messages)
    return message


async def daily_question():
    text = "Напиши один интересный вопрос, который можно задать картам таро. Пример: Как мне достичь поставленной цели? "\
           "Также разбей этот вопрос на три подвопроса для трех позиций карт в триплете. Пример: Первая позиция: (конкретный вопрос,"\
           " раскрывающий главный вопрос) Вторая позиция: (конкретный вопрос, раскрывающий главный вопрос) "\
           "Третья позиция: (конкретный вопрос, раскрывающий главный вопрос) Вопросы могут быть разными, главное чтобы "\
           "они раскрывали главный вопрос. Позиции также могут быть разнообразными, они не должны повторяться. Не добавляй ничего лишнего, только вопросы."

    messages = [
        {'role': 'system',
         'content': 'Ты помощник в трактовках карт таро, ты знаешь все трактовки карт таро по Уэйту и умеешь объяснять их. '
                    'Твой стиль прост и повседневен, но не лишен глубокомыслия. Ты умеешь приводить повседневные примеры из жизни в трактовках карт.'},
        {'role': 'user', 'content': text}
    ]

    message = await asyncio.to_thread(get_gpt_response, messages)
    message = f"<b>ТРИПЛЕТ ДНЯ</b>\n\n{message}\n\n — Пишем <b>'триплет'</b> в комментариях и трактуем его по позициям!"
    await bot.send_message(CHANNEL_ID, message, parse_mode = "HTML")


async def random_card():
    num = randint(0, 77)
    name = execute_select("SELECT name FROM cards WHERE number = ?;", (num,))

    text = f"Напиши интересную трактовку карты Таро {name} по Уэйту на любую тему. Приведи повседневные примеры того, как карта может проигрываться. Не более 500 символов."

    messages = [
        {'role': 'system',
         'content': 'Ты помощник в трактовках карт таро, ты знаешь все трактовки карт таро по Уэйту и умеешь объяснять их. '
                    'Твой стиль прост и повседневен, но не лишен глубокомыслия. Ты умеешь приводить повседневные примеры из '
                    'жизни в трактовках карт.'},
        {'role': 'user', 'content': text}
    ]

    message = await asyncio.to_thread(get_gpt_response, messages)
    message = f"<b>НЕМНОГО О...</b>\n\n{message}"
    await bot.send_message(CHANNEL_ID, message, parse_mode = "HTML")


async def time_spread(num, time, theme=None):
    cards = []
    for card in num:
        name = execute_select("SELECT name FROM cards WHERE number = ?;", (card,))
        cards.append(name)

    if theme is None:
        text = f"Напиши трактовку расклада на картах таро Уэйта. Первая позиция: Карта на {time} - {cards[0]}. Расскажи, как эта карта может описывать {time} в целом, какие энергии будут преследовать меня, а также приведи повседневные примеры того, как карта может проиграться. Вторая позиция: Угроза на {time} - {cards[1]}. Расскажи, как эта карта может проигрываться в виде угрозы на {time}, приведи повседневные примеры. Третья позиция: Совет на {time} - {cards[2]}. Расскажи, как эта карта может проигрываться в виде совета. Приведи повседневные примеры, а также объясни, как можно по совету обезопасить себя от угрозы. Вся трактовка не должна быть более 1000 символов. Стиль дружелюбный, понятный, дружеский, кроме трактовки ничего более не пиши, никаких предупреждений и никаких любезностей. Все должно быть четко и по делу."
    else:
        text = f"Напиши трактовку расклада на картах таро Уэйта на тему {theme} на {time}. Карты: {', '.join(cards)} Расскажи, как эти карты могут описывать происходящую тему в течение заданного периода, какие события могут произойти, как человек может себя чувствовать, приведи повседневные примеры того, как эти карты могут проиграться в заданной теме. Не более 500 символов."

    messages = [
        {'role': 'system',
         'content': 'Ты помощник в трактовках карт таро, ты знаешь все трактовки карт таро по Уэйту и умеешь объяснять их. Твой стиль прост и повседневен, но не лишен глубокомыслия. Ты умеешь приводить повседневные примеры из жизни в трактовках карт.'},
        {'role': 'user', 'content': text}
    ]

    message = await asyncio.to_thread(get_gpt_response, messages)
    return message
