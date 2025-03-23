import datetime
import pytz
from aiogram import Router, Bot
from database import execute_query, execute_select_all
from events.subscriptions.getInvoice import get_sub_type_keyboard

router = Router()


async def check_subscriptions(bot: Bot):
    users = await execute_select_all("select user_id, subscription_date from users where subscription is not 0")
    now = datetime.datetime.now(pytz.timezone('Europe/Kiev'))

    for user in users:
        user_id = user['user_id']
        subscription_date = datetime.datetime.strptime(user['subscription_date'], "%d.%m").replace(year = now.year)

        if (now - subscription_date).days >= 30:
            await execute_query("update users set subscription = 0, subscription_date = null where user_id = $1",
                                (user_id,))
            sub_keyboard = await get_sub_type_keyboard()
            await bot.send_message(user_id, "Ваша подписка истекла. Пожалуйста, оформите новую подписку",
                                   reply_markup = sub_keyboard.as_markup())
