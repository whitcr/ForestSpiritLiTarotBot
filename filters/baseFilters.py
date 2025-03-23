from aiogram.types import CallbackQuery, Message
from aiogram.filters import BaseFilter
from config import load_config
from database import execute_select

config = load_config()
admin_id = config.tg_bot.admin_id
channel_id = config.tg_bot.channel_id


class IsReply(BaseFilter):
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        try:
            return callback_query.from_user.id == callback_query.message.reply_to_message.from_user.id
        except:
            return False


class IsAdmin(BaseFilter):
    async def __call__(self, message) -> bool:
        return message.from_user.id == admin_id


class IsChannel(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == channel_id


class IsBooster(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return await execute_select("SELECT boosted FROM users WHERE user_id = $1", (message.from_user.id,)) >= 1


class IsPrivate(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"


class IsGroup(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "group"


class IsChat(BaseFilter):
    async def __call__(self, message: Message, chat_id) -> bool:
        return message.chat.id == chat_id
