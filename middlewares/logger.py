from typing import Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware

from aiogram.types import Update, CallbackQuery
import logging
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.utils.markdown import hlink

from middlewares.statsHandler import process_callback_data_to_name

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):

    async def __call__(self, handler: Callable, event: Update, data: Dict):

        try:
            result = await handler(event, data)
            if result is UNHANDLED:
                return result

            bot = data.get("bot")
            admin_id = data.get("admin_id")
            user = data.get('event_from_user')
            chat = data.get('event_chat')
            user_id = user.id if user else 'Неизвестный пользователь'
            user_link = f"tg://user?id={user_id}" if user_id != 'Неизвестный пользователь' else 'Неизвестный пользователь'
            chat_id = chat.id if chat else 'Неизвестный чат'
            chat_title = chat.title if chat.title else 'Личка'
            chat_us = chat.username if chat.username else ''

            command_name = event.message if event.message is not None else event.callback_query.data

            if isinstance(event, CallbackQuery):
                command_name = await process_callback_data_to_name(command_name)

            message = f"Получен запрос #{event.update_id}:\n"\
                      f"Пользователь: {hlink(f'{user_id}', user_link)}\n"\
                      f"Чат: {chat_id} - {chat_title} - {chat_us}\n"\
                      f"Команда:  {command_name}\n"

            logging.info(message)

            if bot:
                await bot.send_message(admin_id, message)

            return result
        except Exception as e:

            bot = data.get("bot")
            admin_id = data.get("admin_id")
            user = data.get('event_from_user')
            chat = data.get('event_chat')
            user_id = user.id if user else 'Неизвестный пользователь'
            user_link = f"tg://user?id={user_id}" if user_id != 'Неизвестный пользователь' else 'Неизвестный пользователь'
            chat_id = chat.id if chat else 'Неизвестный чат'
            chat_title = chat.title if chat.title else 'Личка'
            chat_us = chat.username if chat.username else ''
            command = getattr(event.message, 'text', 'Неизвестная команда')

            message = (
                f"Ошибка при выполнении запроса #{event.update_id}:\n"
                f"Пользователь: {hlink(f'{user_id}', user_link)}\n"
                f"Чат: {chat_id} - {chat_title} - {chat_us}\n"
                f"Команда: {command}\n"
                f"Хендлер: {handler.__name__}\n"
                f"Тип ошибки: {type(e).__name__}\n"
                f"Сообщение: {str(e)}\n\n"
            )

            logging.exception(message)

            if bot:
                await bot.send_message(admin_id, message)
