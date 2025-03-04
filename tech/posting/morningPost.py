from constants import FONT_L
from PIL import Image, ImageDraw
import textwrap
from aiogram import types, Router, F
from database import execute_select
from filters.baseFilters import IsAdmin
from functions.affirmations.affirmations import get_random_affirmations
from functions.cards.create import get_path_cards, text_size, get_buffered_image
from functions.gpt.requests import daily_question
from other.phrases import get_random_phrases
from constants import P_FONT_L, P_FONT_XL, P_FONT_S
from tech.posting.moonInfo import moon_posting
from tech.posting.templates import get_post_template

router = Router()


@router.callback_query(IsAdmin(), F.data == 'morning_posting')
async def get_morning_posting(call: types.CallbackQuery):
    await call.answer()
    await morning_posting()


async def morning_posting(bot, channel_id):
    text, day_arcane, day_advice, moon_day, moon_day_text, current_h, pad = await moon_posting()

    image = await get_post_template()

    draw = ImageDraw.Draw(image)
    draw.text((850, 15), 'СЕГОДНЯ', font = P_FONT_L, fill = 'white')

    arcane = f"Аркан дня: {day_arcane}"
    para = textwrap.wrap(arcane, width = 30)
    for line in para:
        draw.text((230, 130), f"{line}\n\n", font = P_FONT_S)

    draw.text((220, 950), f'{moon_day} лунный день', font = P_FONT_L, fill = 'white')

    num = await execute_select("SELECT number FROM meaning_raider WHERE name = $1;", (day_arcane.lower(),))

    card_path = await get_path_cards('raider', num)
    card_path = Image.open(card_path)
    card_path = card_path.resize((450, 730))
    image.paste(card_path, (200, 200))

    para = textwrap.wrap(text, width = 20)
    for line in para:
        w, h = text_size(line, FONT_L)
        draw.text(((2200 - w) / 2, current_h), f"{line}\n\n", font = P_FONT_XL)
        current_h += h + pad

    affirmations = await get_random_affirmations(2)

    day_affirmations = f"— <i>{affirmations[0]}\n\n— {affirmations[1]}</i>\n"

    phrase = await get_random_phrases(1)

    daily_questions = await daily_question()

    text = f"<b><u>Аркан дня: {day_arcane}</u></b>\n{day_advice}\n\
    <b><u>{moon_day} лунный день</u></b>\n{moon_day_text}<b><u>Аффирмации дня</u></b>"\
           f"\n{day_affirmations}\n<b><u>Совет от Ли</u></b>\n{phrase[0]}\n\n<b><u>Вопрос дня</u></b>\n{daily_questions}\n\n—  Не забываем писать в комментариях <b>'Расклад дня'</b>, чтобы получить персональный прогноз на день от Ли!"

    await bot.send_photo(channel_id, await get_buffered_image(image), caption = text)
