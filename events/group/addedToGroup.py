from aiogram import F, Router, Bot
from aiogram.filters.chat_member_updated import\
    ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR
from aiogram.types import ChatMemberUpdated
from aiogram.exceptions import TelegramAPIError

router = Router()
router.my_chat_member.filter(F.chat.type.in_({"group", "supergroup"}))


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed = IS_NOT_MEMBER >> ADMINISTRATOR
    )
)
async def bot_added_as_admin(event: ChatMemberUpdated, bot: Bot):
    try:
        await bot.send_message(
            chat_id = event.chat.id,
            text = f"Спасибо, что добавили меня в "
                   f'"{event.chat.title}" '
                   f"как администратора."
        )
    except TelegramAPIError:
        pass


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed = IS_NOT_MEMBER >> MEMBER
    )
)
async def bot_added_as_member(event: ChatMemberUpdated, bot: Bot):
    try:
        chat_info = await bot.get_chat(event.chat.id)
        if chat_info.permissions.can_send_messages:
            await bot.send_message(
                chat_id = event.chat.id,
                text = f"Привет! Если вы хотите, чтобы я делал вам раскладики, сделайте меня администратором."
            )
    except TelegramAPIError:
        pass
