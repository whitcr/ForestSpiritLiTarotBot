import asyncio
from functools import wraps
from aiogram.types import Message, CallbackQuery


async def get_reply_message(obj):
    if isinstance(obj, Message):
        return getattr(obj.reply_to_message, 'message_id', None) or obj.message_id
    elif isinstance(obj, CallbackQuery):
        return getattr(obj.message.reply_to_message, 'message_id', None) or obj.message.message_id
    return None


async def get_chat_id(obj):
    if isinstance(obj, Message):
        return getattr(obj.chat, 'id', None) or obj.message_id
    elif isinstance(obj, CallbackQuery):
        return getattr(obj.message.chat, 'id', None) or obj.message.message_id
    return None


def typing_animation_decorator(initial_message):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            message = args[0]
            bot = message.bot
            chat_id = message.chat.id

            typing_animation_task = asyncio.create_task(
                animate_typing(chat_id, initial_message, bot)
            )
            try:
                await func(*args, **kwargs)
            finally:
                typing_animation_task.cancel()
                try:
                    await typing_animation_task
                except asyncio.CancelledError:
                    pass

        return wrapper

    return decorator


async def animate_typing(chat_id, initial_message, bot):
    typing_message = await bot.send_message(chat_id = chat_id, text = initial_message)
    try:
        while True:
            await bot.send_chat_action(chat_id, 'typing')
            for i in range(1, 4):
                await asyncio.sleep(i / 2)
                await typing_message.edit_text(f"{initial_message}{'.' * i}")
    except asyncio.CancelledError:
        await typing_message.delete()
        raise


async def delete_message(message, sleep_time: int = 0) -> None:
    if sleep_time > 0:
        await asyncio.sleep(sleep_time)
    await message.delete()


async def timeout_state_finish(state, sleep_time: int = 0) -> None:
    await asyncio.sleep(sleep_time)
    await state.finish()
