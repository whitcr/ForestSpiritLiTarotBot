from aiogram import types, Router, F, Bot
from database import execute_query
from keyboard import follow_daily_mailing_keyboard
import keyboard as kb

router = Router()


@router.message(F.text.lower() == "рассылка")
async def day_follow(message: types.Message):
    await message.reply("Какую информацию вы хотите получать ежедневно?",
                        reply_markup = follow_daily_mailing_keyboard)


@router.callback_query(F.data.endswith('follow_yes'))
async def daily_follow_yes(call: types.CallbackQuery, bot: Bot):
    follow_type = call.data.replace('_yes', '')
    reply_markup = getattr(kb, f"{follow_type}_no_keyboard", None)

    try:
        await call.answer()
        await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                    text = "Вы подписались!", reply_markup = reply_markup)
        await execute_query(
            "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id",
            (call.from_user.id,))
        await execute_query(f"UPDATE users SET {follow_type} = 1 WHERE user_id = $1;", (call.from_user.id,))
    except Exception as e:
        pass


@router.callback_query(F.data.endswith('follow_no'))
async def daily_follow_no(call: types.CallbackQuery, bot: Bot):
    follow_type = call.data.replace('_no', '')
    try:
        await call.answer()
        await bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id,
                                    text = "Позорник!")
        execute_query(f"UPDATE users SET {follow_type} = 0 WHERE user_id = $1;", (call.from_user.id,))
    except Exception as e:
        pass
