import os
from random import randint
from aiogram import Router
from database import execute_select
from functions.gpt.prompts import TAROT_READING_PROMPT, TAROT_ASSISTANT_SYSTEM_PROMPT, TAROT_DAY_READING_PROMPT,\
    TAROT_READING_DETAILS_PROMPT, DAILY_QUESTION_PROMPT, RANDOM_CARD_PROMPT, THEMED_TIME_SPREAD_PROMPT,\
    TAROT_ENERGY_DAY_PROMPT, TIME_SPREAD_PROMPT_THEME

from openai import AsyncOpenAI

router = Router()

client = AsyncOpenAI(api_key = os.environ.get("OPENAI_API_KEY"))


async def get_gpt_response(messages):
    response = await client.chat.completions.create(
        messages = messages, model = "gpt-4o-mini"
    )
    return response.choices[0].message.content


async def get_cards_meanings(cards):
    text = TAROT_READING_PROMPT.format(cards = cards)
    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    return await get_gpt_response(messages)


async def get_cards_day_meanings(cards):
    text = TAROT_DAY_READING_PROMPT.format(cards = cards)
    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    return await get_gpt_response(messages)


async def get_cards_meanings_details(cards):
    text = TAROT_READING_DETAILS_PROMPT.format(cards = cards)
    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    return await get_gpt_response(messages)


async def get_text_energy_day(cards):
    text = TAROT_ENERGY_DAY_PROMPT.format(cards = cards)
    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    return await get_gpt_response(messages)


async def daily_question():
    text = DAILY_QUESTION_PROMPT
    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    message = await get_gpt_response(messages)
    # await bot.send_message(CHANNEL_ID, message, parse_mode = "HTML")


async def random_card():
    card_number = randint(0, 77)
    card_name = await execute_select("SELECT name FROM cards WHERE number = $1;", (card_number,))
    text = RANDOM_CARD_PROMPT.format(name = card_name)
    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    message = await get_gpt_response(messages)
    # await bot.send_message(CHANNEL_ID, message, parse_mode = "HTML")


async def time_spread(card_numbers, time_period, theme=None):
    cards = [
        await execute_select("SELECT name FROM cards WHERE number = $1;", (card,))
        for card in card_numbers
    ]

    if theme is None:
        text = TIME_SPREAD_PROMPT_THEME.format(
            time = time_period, cards = cards
        )
    else:
        text = THEMED_TIME_SPREAD_PROMPT.format(
            theme = theme, time = time_period, cards = cards
        )

    messages = [
        {"role": "system", "content": TAROT_ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    return await get_gpt_response(messages)
