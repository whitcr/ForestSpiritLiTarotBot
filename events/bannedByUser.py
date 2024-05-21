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
    execute_query("DELETE FROM users WHERE user_id = %s", (event.from_user.id,))


# @router.my_chat_member(
#     ChatMemberUpdatedFilter(member_status_changed = MEMBER)
# )
# async def user_unblocked_bot(event: ChatMemberUpdated):
#     await event.answer("Привет, рад, что ты меня разблокировал. Не нужно меня банить :)")
from aiogram.filters import ChatMemberUpdatedFilter, KICKED
from aiogram.types import ChatMemberUpdated

# ...

# Этот хэндлер будет срабатывать на блокировку бота пользователем
# @dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed = KICKED))
# async def process_user_blocked_bot(event: ChatMemberUpdated):
#     print(f'Пользователь {event.from_user.id} заблокировал бота')
#
#
# @dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed = MEMBER))
# async def process_user_unblocked_bot(event: ChatMemberUpdated):
#     print(f"Пользователь {event.from_user.id} разблокировал бота")
#     await bot.send_message(chat_id = event.from_user.id,
#                            text = f'{event.from_user.first_name},Добро пожаловать обратно!')
