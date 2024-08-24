from database import execute_select
from handlers.astrology.getMoon import get_moon_today


async def moon_posting():
    moon_zodiac_name, moon_phase, moon_day, moon_visibility = await get_moon_today()

    text = f"{moon_phase}                          \n\nЗнак: {moon_zodiac_name}                 \n\n{moon_visibility}"
    current_h, pad = 350, 65

    if int(moon_day) == 22:
        num = 0;
    elif int(moon_day) > 22:
        num = int(moon_day) - 22
    else:
        num = int(moon_day)
    day_arcane = await execute_select("select name from cards where number={};", (num,))

    day_advice = await execute_select("select day_advice from meaning_raider where number={};", (num,))

    moon_day_text = await execute_select("select text from moon_days where day={};", (moon_day,))

    return text, day_arcane, day_advice, moon_day, moon_day_text, current_h, pad
