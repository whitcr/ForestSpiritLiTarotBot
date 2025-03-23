import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.types import FSInputFile

router = Router()


@router.message(Command("privacy", prefix = "/"))
async def send_privacy_document(message: types.Message, bot: Bot):
    await message.answer_document(
        FSInputFile("images/tech/subs/privacy.pdf"),
        caption = "Покупая подписку, вы соглашаетесь с пользовательским соглашением."
    )


@router.callback_query(F.data.startswith("get_privacy"))
async def send_privacy_document(call: types.CallbackQuery, bot: Bot):
    await call.answer()

    await call.message.answer_document(
        FSInputFile("images/tech/subs/privacy.pdf"),
        caption = "Покупая подписку, вы соглашаетесь с пользовательским соглашением."
    )
