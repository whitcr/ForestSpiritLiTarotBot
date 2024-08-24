from aiogram import F, Router
from aiogram.filters.chat_member_updated import\
    ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.types import ChatMemberUpdated

from database import execute_query

router = Router()
router.my_chat_member.filter(F.chat.type == "private")
router.message.filter(F.chat.type == "private")


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed = KICKED)
)
async def user_blocked_bot(event: ChatMemberUpdated):
    await execute_query("DELETE FROM users WHERE user_id = $1", (event.from_user.id,))


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed = MEMBER)
)
async def user_unblocked_bot(event: ChatMemberUpdated):
    await event.answer("Привет, рад, что ты меня разблокировал. В бане было очень грустно :(")
