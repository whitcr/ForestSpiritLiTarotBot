from random import randint
from aiogram.utils.markdown import hlink

from database import execute_select


async def get_meditation_post(bot, channel_id):
    number = randint(1, 15)
    name = await execute_select("select name from meditation_text where number={}", (number,))

    text = await execute_select("select text from meditation_text where number = {}", (number,))

    rules = hlink('Как медитировать?', 'https://telegra.ph/Pravila-Meditacii-10-16')

    text = f"<b>ВОСКРЕСНАЯ МЕДИТАЦИЯ \n\n {name}</b>\n\n{text}\n\n"\
           f"{rules}"\
           f"\n\n— Делимся впечатлениями от медитации в комментариях!"

    await bot.send_message(channel_id, text = text)
