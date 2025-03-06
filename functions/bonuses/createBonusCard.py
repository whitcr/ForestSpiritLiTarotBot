import io
from PIL import Image, ImageDraw, ImageFont
from aiogram import types, Router, F, Bot

from constants import P_FONT_L
from database import execute_select, execute_select_all
from aiogram.types import BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from events.user.referrals import get_referral_count
from functions.messages.messages import typing_animation_decorator

router = Router()


async def create_large_checkmark(draw, x, y, size=60, color="red", width=6):
    start_x = x - size // 2
    start_y = y
    middle_x = x - size // 6
    middle_y = y + size // 2
    end_x = x + size // 2
    end_y = y - size // 2

    for offset in range(-width // 2, width // 2):
        draw.line(
            [(start_x + offset, start_y),
             (middle_x + offset, middle_y),
             (end_x + offset, end_y - offset)],
            fill = color, width = 3
        )


async def add_db_numbers(draw, width, height, personal_number, friend_number):
    text_personal = f"{personal_number}"
    draw.text(
        (width * 0.74, height * 0.03),
        text_personal,
        fill = "white",
        font = P_FONT_L
    )

    text_friend = f"{friend_number}"
    draw.text(
        (width * 0.66, height * 0.655),
        text_friend,
        fill = "white",
        font = P_FONT_L
    )


async def mark_bonuses(image_path, personal_bonus_number, friend_bonus_number, type):
    img = Image.open(image_path)
    width, height = img.size
    draw = ImageDraw.Draw(img)

    if type == 1:
        personal_bonus_positions = {
            4: (width * 0.2, height * 0.17),  # Расклад на неделю от ли
            12: (width * 0.4, height * 0.17),  # Расклад на месяц от ли
            20: (width * 0.6, height * 0.17),  # Week премиум
            28: (width * 0.8, height * 0.17),  # Month премиум

            # Middle row
            7: (width * 0.25, height * 0.45),  # 20% скидка
            16: (width * 0.5, height * 0.45),  # Free вопрос
            24: (width * 0.75, height * 0.45),  # 2 Free вопроса
        }
    else:
        personal_bonus_positions = {
            1000: (width * 0.2, height * 0.17),  # Расклад на неделю от ли
            4000: (width * 0.4, height * 0.17),  # Расклад на месяц от ли
            8000: (width * 0.6, height * 0.17),  # Week премиум
            15000: (width * 0.8, height * 0.17),  # Month премиум

            # Middle row
            2000: (width * 0.25, height * 0.45),  # 20% скидка
            6000: (width * 0.5, height * 0.45),  # Free вопрос
            10000: (width * 0.75, height * 0.45),  # 2 Free вопроса
        }

    friend_bonus_positions = {
        1: (width * 0.15, height * 0.8),  # 20% скидка
        3: (width * 0.3, height * 0.8),  # Week премиум
        5: (width * 0.45, height * 0.8),  # 2 Free вопроса
        7: (width * 0.6, height * 0.8),  # 3 Free вопроса
        9: (width * 0.75, height * 0.8),  # Month премиум
        12: (width * 0.9, height * 0.8),  # 4 Free вопроса
    }

    for number, position in personal_bonus_positions.items():
        if number <= personal_bonus_number:
            await create_large_checkmark(draw, position[0], position[1])

    for number, position in friend_bonus_positions.items():
        if number <= friend_bonus_number:
            await create_large_checkmark(draw, position[0], position[1])

    await add_db_numbers(draw, width, height, personal_bonus_number, friend_bonus_number)

    return img


@router.callback_query(F.data.startswith("get_bonus_card"))
@typing_animation_decorator(initial_message = "Вычисляю")
async def get_bonus_cards(call: types.CallbackQuery, bot: Bot, channel_id):
    await call.answer()
    result = await execute_select_all(
        "SELECT total_count, paid_spreads, referrals_paid FROM users WHERE user_id = $1",
        (call.from_user.id,))

    spreads_count, paid_count, referrals_paid = result[0]

    referrals_array = await get_referral_count(call.from_user.id, bot, channel_id)

    img1 = await mark_bonuses(
        image_path = "./images/tech/bonusCards/bonusCard1.png",
        personal_bonus_number = paid_count,
        friend_bonus_number = referrals_paid,
        type = 1
    )

    img2 = await mark_bonuses(
        image_path = "./images/tech/bonusCards/bonusCard2.png",
        personal_bonus_number = spreads_count,
        friend_bonus_number = len(referrals_array) if referrals_array else 0,
        type = 2
    )

    with io.BytesIO() as output1, io.BytesIO() as output2:
        img1.save(output1, format = "PNG")
        img2.save(output2, format = "PNG")
        output1.seek(0)
        output2.seek(0)

        media_group = MediaGroupBuilder()

        media_group.add_photo(media = BufferedInputFile(output1.getvalue(), "image.png"))
        media_group.add_photo(media = BufferedInputFile(output2.getvalue(), "image1.png"))

        await call.message.reply_media_group(media = media_group.build())
