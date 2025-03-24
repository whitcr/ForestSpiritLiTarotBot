from aiogram import types, Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hlink

from events.user.referrals import get_referrals
from keyboard import menu_private_keyboard
from tech.activities.contest.contest import contest_with_referral

router = Router()


@router.message(CommandStart(), flags = {"use_user_statistics": True})
async def start(message: types.Message, bot: Bot):
    command_params = message.text

    if "ref_" in command_params:
        await get_referrals(bot, message, command_params)

    if "contest" in command_params:
        await contest_with_referral(message)

    if message.chat.type == "private":
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.reply(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?',
                            reply_markup = menu_private_keyboard)
