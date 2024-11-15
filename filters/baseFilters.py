from aiogram.types import CallbackQuery, Message
from aiogram.filters import BaseFilter
from config import load_config

config = load_config()
admin_id = config.tg_bot.admin_id
channel_id = config.tg_bot.channel_id


class IsReply(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.from_user.id == callback_query.message.reply_to_message.from_user.id


class IsAdmin(BaseFilter):
    async def __call__(self, message) -> bool:
        return message.from_user.id == admin_id


class IsChannel(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == channel_id
