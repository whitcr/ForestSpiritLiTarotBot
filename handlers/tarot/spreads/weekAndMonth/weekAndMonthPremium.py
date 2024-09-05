from aiogram.types import BufferedInputFile

from database import execute_query
from functions.cards.createThreeCards import get_image_three_cards_wb
from functions.messages.messages import typing_animation_decorator
from aiogram import Router, F
from constants import P_FONT_L
from functions.gpt.requests import time_spread
from PIL import ImageDraw
from io import BytesIO

from functions.pdf.createFile import create_pdf

router = Router()


# @router.message(F.text.lower().startswith("тест"))
# @typing_animation_decorator(initial_message = "Раскладываю")
async def get_week_spread_premium(user_id, bot, spread_name):
    spread_name = "месяца" if spread_name == "month" else "недели"

    THEME_MAP = ["Финансы", "Личная Жизнь", "Эмоции"]
    texts = []
    images = []

    image, num = await get_image_three_cards_wb(user_id)
    draw_text = ImageDraw.Draw(image)
    draw_text.text((220, 80), f"Карта {spread_name}", fill = '#1A1A1A', font = P_FONT_L)
    draw_text.text((810, 80), f"Угроза {spread_name}", fill = '#1A1A1A', font = P_FONT_L)
    draw_text.text((1440, 80), f"Совет {spread_name}", fill = '#1A1A1A', font = P_FONT_L)

    temp_img = BytesIO()
    image.save(temp_img, format = 'PNG')
    temp_img.seek(0)
    images.append(temp_img)

    text = await time_spread(num, f"{spread_name}")
    text = f"<b>РАСКЛАД {spread_name}</b>\n\n{text}"
    texts.append(text)

    for THEME in THEME_MAP:
        image, num = await get_image_three_cards_wb(user_id)

        temp_img = BytesIO()
        image.save(temp_img, format = 'PNG')
        temp_img.seek(0)
        images.append(temp_img)

        text = await time_spread(num, f"{spread_name}")
        text = f"<b>{THEME.upper()} {spread_name.upper()}</b>\n\n{text}"
        texts.append(text)

    pdf_buffer = BytesIO()

    background_image = "./images/tech/pdf/bg_pdf.png"

    create_pdf(pdf_buffer, texts, images, background_image = background_image)

    message = await bot.send_document(user_id,
                                      BufferedInputFile(pdf_buffer.getvalue(), filename = f"Расклад {spread_name}.pdf"))
    file_id = message.document.file_id
    table = f"spreads_{spread_name}"
    await execute_query(f"INSERT INTO {table} (user_id, file_id) VALUES (&1, &2)", (user_id, file_id))

    for img in images:
        img.close()
    pdf_buffer.close()
