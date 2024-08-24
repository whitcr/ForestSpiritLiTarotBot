from database import execute_select_all
from main import bot

from handlers.astrology.getMoon import get_moon_today


async def moon_text_follow():
    try:
        text_moon = await get_moon_today()
        ids = await execute_select_all("select user_id from users where moon_follow=1;")
        for user_id_tuple in ids:
            user_id = user_id_tuple[0]
            try:
                await bot.send_message(user_id,
                                       f"Сегодня у нас: <b>{text_moon[1]}</b>\nФаза луны: <b>{text_moon[3]}</b>\nЗнак: <b>{text_moon[5]}</b>\nСозвездие: <b>{text_moon[7]}</b>\nЛунный день: <b>{text_moon[9]}</b>\nВидимость: <b>{text_moon[13]}</b>")
            except:
                await bot.send_message(user_id, "Что-то пошло не так. Попробуйте еще раз.")
    except Exception as e:
        pass
