from typing import Union
from aiogram import types
from database import execute_query, execute_select
import asyncio


async def get_statistic_card(num: Union[int, str]):
    row = execute_select("SELECT quantity FROM statistic_cards WHERE card = %s", (num,))

    if row:
        plus = row[0] + 1
        execute_query("UPDATE statistic_cards SET quantity = %s WHERE card = %s", (plus, num))
    else:
        execute_query("INSERT INTO statistic_cards (card, quantity) VALUES (%s, %s)", (num, 1))


async def get_statistic_users(message: types.Message):
    user_id: int = message.from_user.id
    username: str = message.from_user.username
    try:
        row = execute_select("SELECT quantity FROM users WHERE user_id = %s", (user_id,))

        plus = row[0] + 1
        execute_query("UPDATE users SET quantity = %s WHERE user_id = %s", (plus, user_id))
        execute_query("UPDATE users SET username = %s WHERE user_id = %s", (username, user_id))
    except:
        execute_query("INSERT INTO users (quantity, user_id, username, cards_type) VALUES (%s, %s, %s, %s)",
                      (1, user_id, username, 'raider'))


async def delete_message(message: types.Message, sleep_time: int = 0) -> None:
    if sleep_time > 0:
        await asyncio.sleep(sleep_time)
    await message.delete()


async def timeout_state_finish(state, sleep_time: int = 0) -> None:
    await asyncio.sleep(sleep_time)
    await state.finish()
