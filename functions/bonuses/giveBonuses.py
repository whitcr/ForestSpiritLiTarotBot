from aiogram import types, Router, F, Bot
from database import execute_query
from filters.baseFilters import IsAdmin

router = Router()


@router.message(IsAdmin(), F.text.lower().startswith("++"))
async def handle_admin_command_give_bonuses(message: types.Message, bot: Bot):
    if not message.reply_to_message:
        return
    target_user_id = message.reply_to_message.from_user.id
    print(message.text.strip(" ")[3])
    try:
        value = int(message.text.strip(" ")[3])
    except ValueError:
        await message.reply("Неверный формат команды. Используйте ++ число.")
        return

    command = message.text.strip().lower()

    if command.startswith("++") and "расклад" in command:
        await execute_query("UPDATE users SET paid_spreads = paid_spreads + $1 WHERE user_id = $2",
                            (value, target_user_id))
        await message.reply(f"Расклад в кол-ве {value} успешно добавлен пользователю {target_user_id}.")
    elif command.startswith("++") and "друг" in command:
        await execute_query("UPDATE users SET referrals_paid = referrals_paid + $1 WHERE user_id = $2",
                            (value, target_user_id))
        await message.reply(f"Друг в кол-ве {value} успешно добавлен пользователю {target_user_id}.")
    else:
        await message.reply("Неизвестная команда.")
