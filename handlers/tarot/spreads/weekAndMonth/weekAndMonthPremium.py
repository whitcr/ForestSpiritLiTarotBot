from aiogram.types import BufferedInputFile

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
@typing_animation_decorator(initial_message = "Раскладываю")
async def get_week_spread_premium(user_id, bot):
    THEME_MAP = ["Финансы", "Личная Жизнь", "Эмоции"]
    texts = []
    images = []

    image, num = await get_image_three_cards_wb(user_id)
    draw_text = ImageDraw.Draw(image)
    draw_text.text((220, 80), f"Карта недели", fill = '#1A1A1A', font = P_FONT_L)
    draw_text.text((810, 80), f"Угроза недели", fill = '#1A1A1A', font = P_FONT_L)
    draw_text.text((1440, 80), f"Совет недели", fill = '#1A1A1A', font = P_FONT_L)

    temp_img = BytesIO()
    image.save(temp_img, format = 'PNG')
    temp_img.seek(0)
    images.append(temp_img)

    text = await time_spread(num, "неделю")
    text = f"<b>РАСКЛАД НА НЕДЕЛЮ</b>\n\n{text}"
    texts.append(text)

    for THEME in THEME_MAP:
        image, num = await get_image_three_cards_wb(user_id)

        temp_img = BytesIO()
        image.save(temp_img, format = 'PNG')
        temp_img.seek(0)
        images.append(temp_img)

        text = await time_spread(num, "неделю")
        text = f"<b>{THEME.upper()} на неделю</b>\n\n{text}"
        texts.append(text)

    pdf_buffer = BytesIO()

    background_image = "./cards/tech/pdf/bg_pdf.png"

    create_pdf(pdf_buffer, texts, images, background_image = background_image)

    await bot.send_document(user_id, BufferedInputFile(pdf_buffer.getvalue(), filename = "spread.pdf"))

    for img in images:
        img.close()
    pdf_buffer.close()
