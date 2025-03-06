from aiogram import types, Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import execute_query, execute_select_all
from filters.baseFilters import IsReply
from filters.subscriptions import SubscriptionLevel

router = Router()


async def generate_mail_kb(user_id):
    user_data = await execute_select_all(
        "SELECT moon_follow, day_card_follow, week_card_follow, month_card_follow FROM users WHERE user_id = $1;",
        (user_id,))

    if not user_data:
        return None

    moon_follow, day_card_follow, week_card_follow, month_card_follow = user_data[0]

    keyboard = InlineKeyboardBuilder()

    def toggle_button(label, status, follow_type):
        callback_data = f"{follow_type}_{'no' if status else 'yes'}"
        keyboard.button(text = f"{label} {'🟢' if status else '🔴'}", callback_data = callback_data)

    toggle_button("Луна", moon_follow, "moon_follow")
    toggle_button("Расклад дня", day_card_follow, "day_card_follow")
    toggle_button("Расклад на неделю", week_card_follow, "week_card_follow")
    toggle_button("Расклад на месяц", month_card_follow, "month_card_follow")

    keyboard.adjust(2)  # Делаем 2 кнопки в ряд

    return keyboard.as_markup()


@router.message(F.text.lower() == "рассылка", SubscriptionLevel(1))
async def day_follow(message: types.Message):
    keyboard = await generate_mail_kb(message.from_user.id)
    if keyboard:
        await message.reply("Какую информацию вы хотите получать ежедневно?\n 🟢 - включить, 🔴 - выключить",
                            reply_markup = keyboard)


@router.callback_query(IsReply(), F.data.startswith('get_mailing'), SubscriptionLevel(1))
async def day_follow_cb(call: types.CallbackQuery):
    await call.answer()
    keyboard = await generate_mail_kb(call.message.reply_to_message.from_user.id)
    if keyboard:
        await call.message.reply("Какую информацию вы хотите получать ежедневно?\n 🟢 - включить, 🔴 - выключить",
                                 reply_markup = keyboard)


@router.callback_query(IsReply(), F.data.endswith('follow_yes') | F.data.endswith('follow_no'))
async def toggle_subscription(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    follow_type, action = call.data.rsplit('_', 1)
    new_status = 1 if action == 'yes' else 0

    await execute_query(f"UPDATE users SET {follow_type} = {new_status} WHERE user_id = $1;", (call.from_user.id,))

    keyboard = await generate_mail_kb(call.from_user.id)
    if keyboard:
        await call.message.edit_text("Какую информацию вы хотите получать ежедневно?\n 🟢 - включить, 🔴 - выключить",
                                     reply_markup = keyboard)
