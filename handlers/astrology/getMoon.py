from aiogram import types, Router, F
import requests
from bs4 import BeautifulSoup
from random import randint
from database import execute_select, execute_select_all
from filters.subscriptions import SubscriptionLevel
from middlewares.statsUser import UserStatisticsMiddleware

router = Router()
router.message.middleware(UserStatisticsMiddleware())
router.callback_query.middleware(UserStatisticsMiddleware())


@router.message(F.text.lower() == "совет луны", SubscriptionLevel(1), flags = {"use_user_statistics": True})
async def get_moon_advice(message: types.Message):
    num = randint(0, 43)
    result = await execute_select_all("SELECT advice, name FROM moon_advice WHERE number = $1",
                                      (num,))

    await message.answer(f'<b>{result[0][0]}</b> \n \n{result[0][1]}')


async def get_moon_today():
    url = "https://mirkosmosa.ru/lunar-calendar"
    try:
        r = requests.get(url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")

        moon_zodiac_name = soup.select_one('.moon-zodiac_name')
        moon_phase = soup.select_one('.phase_data')
        moon_day = soup.select_one('.moon-age_sym')
        moon_visibility = soup.select_one('.illum')

        if any(elem is None for elem in [moon_zodiac_name, moon_phase, moon_day, moon_visibility]):
            raise ValueError("Unable to find required elements on the page.")

        return (moon_zodiac_name.text, moon_phase.text, moon_day.text, moon_visibility.text)

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error: {e}")
        return None


@router.message(F.text.lower() == "луна", SubscriptionLevel(1), flags = {"use_user_statistics": True})
async def get_moon_text(message: types.Message):
    moon_data = await get_moon_today()
    if moon_data:
        moon_zodiac_name, moon_phase, moon_day, moon_visibility = moon_data
        text = f"Фаза луны: <b>{moon_phase}</b>\nЗнак: <b>{moon_zodiac_name}</b>"\
               f"\nЛунный день: <b>{moon_day}</b>\nВидимость: <b>{moon_visibility}</b>"
        await message.answer(text)
    else:
        await message.answer("Луна в ауте, попробуй позже.")
