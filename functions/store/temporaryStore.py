import time
import asyncio
from aiogram import types

data_store = {}


async def store_data(message: types.Message, num1=None, num2=None):
    message_id = message.message_id
    chat_id = message.chat.id
    timestamp = time.time()

    if num2 is None:
        data = {'chat_id': chat_id, 'num1': num1, 'timestamp': timestamp}
    elif num1 is not None and num2 is not None:
        data = {'chat_id': chat_id, 'num1': num1, 'num2': num2, 'timestamp': timestamp}
    else:
        return None

    data_store[message_id] = data


async def get_data(message_id):
    message_data = data_store.get(message_id)
    print(message_data)
    if message_data:
        return message_data['num1']
    else:
        return None


async def get_data_two_nums(message_id):
    message_data = data_store.get(message_id)
    if message_data and 'num1' in message_data and 'num2' in message_data:
        return message_data['num1'], message_data['num2']
    else:
        return None


async def delete_expired_data():
    while True:
        await asyncio.sleep(1200)
        expired_message_ids = [message_id for message_id, message_data in data_store.items() if
                               time.time() - message_data['timestamp'] >= 1200]

        for message_id in expired_message_ids:
            data_store.pop(message_id, None)
