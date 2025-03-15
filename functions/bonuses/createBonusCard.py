import io
from PIL import Image, ImageDraw, ImageFont
from aiogram import types, Router, F, Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from constants import P_FONT_L
from database import execute_select, execute_select_all, execute_query
from events.user.referrals import get_referral_count, get_names_from_array_ids
from functions.messages.messages import typing_animation_decorator

router = Router()


# Optimized callback data classes
class BonusCardCallbackFactory(CallbackData, prefix = "bcard"):
    action: str  # "view" or "back"
    bonus_type: str  # "li" or "paid"


class BonusActionCallbackFactory(CallbackData, prefix = "bact"):
    action: str  # "confirm" or "activate"
    type: str  # "li" or "paid"
    cat: str  # "p" (personal) or "r" (referral)
    idx: int  # The index in the bonus array


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

        friend_bonus_positions = {
            1: (width * 0.15, height * 0.8),  # 20% скидка
            3: (width * 0.3, height * 0.8),  # Week премиум
            5: (width * 0.45, height * 0.8),  # 2 Free вопроса
            7: (width * 0.6, height * 0.8),  # 3 Free вопроса
            9: (width * 0.75, height * 0.8),  # Month премиум
            12: (width * 0.9, height * 0.8),  # 4 Free вопроса
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
            3: (width * 0.15, height * 0.8),  # 20% скидка
            6: (width * 0.3, height * 0.8),  # Week премиум
            9: (width * 0.45, height * 0.8),  # 2 Free вопроса
            12: (width * 0.6, height * 0.8),  # 3 Free вопроса
            15: (width * 0.75, height * 0.8),  # Month премиум
            18: (width * 0.9, height * 0.8),  # 4 Free вопроса
        }

    for number, position in personal_bonus_positions.items():
        if number <= personal_bonus_number:
            await create_large_checkmark(draw, position[0], position[1])

    for number, position in friend_bonus_positions.items():
        if number <= friend_bonus_number:
            await create_large_checkmark(draw, position[0], position[1])

    await add_db_numbers(draw, width, height, personal_bonus_number, friend_bonus_number)

    return img


# Define bonuses and their thresholds with confirmation messages
PERSONAL_PAID_BONUSES = [
    {
        "name": "Расклад на неделю от Ли",
        "threshold": 4,
        "function": "activate_weekly_spread",
        "confirm_message": "Вы собираетесь активировать бонус «Расклад на неделю от Ли».\n\nРасклад будет подготовлен Ли и доступен в вашем личном кабинете в течение 24 часов. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "20% скидка",
        "threshold": 7,
        "function": "activate_discount_20",
        "confirm_message": "Вы собираетесь активировать бонус «20% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Расклад на месяц от Ли",
        "threshold": 12,
        "function": "activate_monthly_spread",
        "confirm_message": "Вы собираетесь активировать бонус «Расклад на месяц от Ли».\n\nРасклад будет подготовлен Ли и доступен в вашем личном кабинете в течение 24 часов. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Free вопрос",
        "threshold": 16,
        "function": "activate_free_question",
        "confirm_message": "Вы собираетесь активировать бонус «Free вопрос».\n\n1 бесплатный вопрос будет добавлен в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Week премиум",
        "threshold": 20,
        "function": "activate_week_premium",
        "confirm_message": "Вы собираетесь активировать бонус «Week премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 7 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "2 Free вопроса",
        "threshold": 24,
        "function": "activate_two_free_questions",
        "confirm_message": "Вы собираетесь активировать бонус «2 Free вопроса».\n\n2 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Month премиум",
        "threshold": 28,
        "function": "activate_month_premium",
        "confirm_message": "Вы собираетесь активировать бонус «Month премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
]

FRIEND_PAID_BONUSES = [
    {
        "name": "20% скидка",
        "threshold": 1,
        "function": "activate_discount_20",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «20% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Week премиум",
        "threshold": 3,
        "function": "activate_week_premium",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «Week премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 7 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "2 Free вопроса",
        "threshold": 5,
        "function": "activate_two_free_questions",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «2 Free вопроса».\n\n2 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "3 Free вопроса",
        "threshold": 7,
        "function": "activate_three_free_questions",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «3 Free вопроса».\n\n3 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Month премиум",
        "threshold": 9,
        "function": "activate_month_premium",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «Month премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "4 Free вопроса",
        "threshold": 12,
        "function": "activate_four_free_questions",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «4 Free вопроса».\n\n4 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
]

PERSONAL_LI_BONUSES = [
    {
        "name": "10% скидка",
        "threshold": 1000,
        "function": "activate_discount_10",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «10% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "20% скидка",
        "threshold": 2000,
        "function": "activate_discount_20",
        "confirm_message": "Вы собираетесь активировать бонус «20% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Free вопрос",
        "threshold": 4000,
        "function": "activate_free_question",
        "confirm_message": "Вы собираетесь активировать бонус «Free вопрос».\n\n1 бесплатный вопрос будет добавлен в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "50% скидка",
        "threshold": 6000,
        "function": "activate_discount_50",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «20% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Week премиум",
        "threshold": 8000,
        "function": "activate_week_premium",
        "confirm_message": "Вы собираетесь активировать бонус «Week премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 14 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "2 Free вопроса",
        "threshold": 10000,
        "function": "activate_two_free_questions",
        "confirm_message": "Вы собираетесь активировать бонус «2 Free вопроса».\n\n2 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Month премиум",
        "threshold": 15000,
        "function": "activate_month_premium",
        "confirm_message": "Вы собираетесь активировать бонус «Month премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
]

FRIEND_LI_BONUSES = [
    {
        "name": "Week премиум",
        "threshold": 3,
        "function": "activate_week_premium",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «Week премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 7 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "50% скидка",
        "threshold": 6,
        "function": "activate_discount_50",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «20% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Free вопрос",
        "threshold": 9,
        "function": "activate_free_question",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «2 Free вопроса».\n\n2 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "50% скидка",
        "threshold": 12,
        "function": "activate_discount_50",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «20% скидка».\n\nСкидка будет автоматически применена к вашему следующему заказу в течение 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "2 Free вопроса",
        "threshold": 15,
        "function": "activate_two_free_questions",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «4 Free вопроса».\n\n4 бесплатных вопроса будут добавлены в ваш личный кабинет. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },
    {
        "name": "Month премиум",
        "threshold": 18,
        "function": "activate_month_premium",
        "confirm_message": "Вы собираетесь активировать реферальный бонус «Month премиум».\n\nПремиум статус будет автоматически добавлен на ваш аккаунт на 30 дней. После активации бонус будет использован и недоступен для повторного использования.\n\nПодтвердить активацию?"
    },

]


async def check_and_update_bonuses(user_id, paid_count, spreads_count, referrals_paid, referrals_array):
    # Get current bonus status
    result = await execute_select_all(
        "SELECT bonuses_li, bonuses_paid FROM users WHERE user_id = $1",
        (user_id,)
    )

    bonuses_li, bonuses_paid = result[0]

    # If columns don't exist or are NULL, create them with default values
    if bonuses_li is None:
        bonuses_li = "1" * 13
        await execute_query(
            "UPDATE users SET bonuses_li = $1 WHERE user_id = $2",
            (bonuses_li, user_id)
        )

    if bonuses_paid is None:
        bonuses_paid = "1" * 13
        await execute_query(
            "UPDATE users SET bonuses_paid = $1 WHERE user_id = $2",
            (bonuses_paid, user_id)
        )

    # Convert strings to lists for easier manipulation
    bonuses_li_list = list(bonuses_li)
    bonuses_paid_list = list(bonuses_paid)

    # Check personal LI bonuses (first 7 positions)
    for i, bonus in enumerate(PERSONAL_PAID_BONUSES):
        if paid_count >= bonus["threshold"] and bonuses_paid_list[i] == "1":
            bonuses_paid_list[i] = "2"  # Mark as available

    # Check friend LI bonuses (next 6 positions)
    for i, bonus in enumerate(FRIEND_PAID_BONUSES):
        if referrals_paid >= bonus["threshold"] and bonuses_paid_list[i + 7] == "1":
            bonuses_paid_list[i + 7] = "2"  # Mark as available

    # Check personal PAID bonuses (first 7 positions)
    for i, bonus in enumerate(PERSONAL_LI_BONUSES):
        if spreads_count >= bonus["threshold"] and bonuses_li_list[i] == "1":
            bonuses_li_list[i] = "2"  # Mark as available

    # Check friend PAID bonuses (next 6 positions)
    for i, bonus in enumerate(FRIEND_LI_BONUSES):
        if referrals_array >= bonus["threshold"] and bonuses_li_list[i + 7] == "1":
            bonuses_li_list[i + 7] = "2"  # Mark as available

    # Convert lists back to strings
    new_bonuses_li = "".join(bonuses_li_list)
    new_bonuses_paid = "".join(bonuses_paid_list)

    # Update the database if changes were made
    if new_bonuses_li != bonuses_li or new_bonuses_paid != bonuses_paid:
        await execute_query(
            "UPDATE users SET bonuses_li = $1, bonuses_paid = $2 WHERE user_id = $3",
            (new_bonuses_li, new_bonuses_paid, user_id)
        )

    return new_bonuses_li, new_bonuses_paid


def create_bonus_keyboard(bonus_type, bonuses_status):
    keyboard = []
    if bonus_type == "li":
        # First 7 positions are personal LI bonuses
        for i, bonus in enumerate(PERSONAL_LI_BONUSES):
            status = bonuses_status[i]
            if status == "2":  # Available
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✅ {bonus['name']} (Доступен)",
                        callback_data = BonusActionCallbackFactory(
                            action = "confirm",
                            type = "li",
                            cat = "p",  # personal
                            idx = i
                        ).pack()
                    )
                ])
            elif status == "3":  # Used
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✓ {bonus['name']} (Использован)",
                        callback_data = "none"
                    )
                ])

        # Next 6 positions are friend LI bonuses
        for i, bonus in enumerate(FRIEND_LI_BONUSES):
            status = bonuses_status[i + 7]
            if status == "2":  # Available
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✅ {bonus['name']} (Реферальный, доступен)",
                        callback_data = BonusActionCallbackFactory(
                            action = "confirm",
                            type = "li",
                            cat = "r",  # referral
                            idx = i + 7
                        ).pack()
                    )
                ])
            elif status == "3":  # Used
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✓ {bonus['name']} (Реферальный, использован)",
                        callback_data = "none"
                    )
                ])
    else:  # paid
        # First 7 positions are personal PAID bonuses
        for i, bonus in enumerate(PERSONAL_PAID_BONUSES):
            status = bonuses_status[i]
            if status == "2":  # Available
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✅ {bonus['name']} (Доступен)",
                        callback_data = BonusActionCallbackFactory(
                            action = "confirm",
                            type = "paid",
                            cat = "p",  # personal
                            idx = i
                        ).pack()
                    )
                ])
            elif status == "3":  # Used
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✓ {bonus['name']} (Использован)",
                        callback_data = "none"
                    )
                ])

        # Next 6 positions are friend PAID bonuses
        for i, bonus in enumerate(FRIEND_PAID_BONUSES):
            status = bonuses_status[i + 7]
            if status == "2":  # Available
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✅ {bonus['name']} (Реферальный, доступен)",
                        callback_data = BonusActionCallbackFactory(
                            action = "confirm",
                            type = "paid",
                            cat = "r",  # referral
                            idx = i + 7
                        ).pack()
                    )
                ])
            elif status == "3":  # Used
                keyboard.append([
                    InlineKeyboardButton(
                        text = f"✓ {bonus['name']} (Реферальный, использован)",
                        callback_data = "none"
                    )
                ])

    return InlineKeyboardMarkup(inline_keyboard = keyboard)


# Create confirmation keyboard
def create_confirmation_keyboard(bonus_type, bonus_category, bonus_index):
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text = "✅ Да, активировать",
                    callback_data = BonusActionCallbackFactory(
                        action = "activate",
                        type = bonus_type,
                        cat = bonus_category,
                        idx = bonus_index
                    ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text = "🔙 Отмена",
                    callback_data = BonusCardCallbackFactory(
                        action = "view",
                        bonus_type = bonus_type
                    ).pack()
                )
            ]
        ]
    )


@router.callback_query(F.data.startswith("get_bonus_card"))
@typing_animation_decorator(initial_message = "Вычисляю")
async def get_bonus_cards(call: types.CallbackQuery, bot: Bot, channel_id):
    if call.message.chat.type == "private":
        await call.answer()

        # Get user stats
        result = await execute_select_all(
            "SELECT total_count, paid_spreads, referrals_paid FROM users WHERE user_id = $1",
            (call.from_user.id,))

        spreads_count, paid_count, referrals_paid = result[0]

        referrals_array, removed = await get_referral_count(call.from_user.id, bot, channel_id)

        # Check and update bonuses
        bonuses_li, bonuses_paid = await check_and_update_bonuses(
            call.from_user.id, paid_count, spreads_count, referrals_paid, referrals_array
        )

        # Create and send bonus card images
        img1 = await mark_bonuses(
            image_path = "./images/tech/bonusCards/bonusCard1.png",
            personal_bonus_number = paid_count,
            friend_bonus_number = referrals_paid,
            type = 1
        )

        img2 = await mark_bonuses(
            image_path = "./images/tech/bonusCards/bonusCard2.png",
            personal_bonus_number = spreads_count,
            friend_bonus_number = referrals_array,
            type = 2
        )

        removed_list = False
        if len(removed) >= 1:
            names = await get_names_from_array_ids(removed, bot)
            removed_list = f"К сожалению, {names} не подписан(ы) на канал и не был(и) засчитан(ы) вам в бонусы."

        with io.BytesIO() as output1, io.BytesIO() as output2:
            img1.save(output1, format = "PNG")
            img2.save(output2, format = "PNG")
            output1.seek(0)
            output2.seek(0)

            await bot.send_photo(
                call.from_user.id,
                BufferedInputFile(output2.getvalue(), "image.png")
            )

            await bot.send_message(
                call.from_user.id,
                text = "Бонусы за расклады и приглашенных друзей в Ли \n\n" + removed_list if removed_list else "",
                reply_markup = create_bonus_keyboard("li", bonuses_li)
            )

            await bot.send_photo(
                call.from_user.id,
                BufferedInputFile(output1.getvalue(), "image1.png")
            )

            await bot.send_message(
                call.from_user.id,
                text = "Бонусы за платные расклады и приглашенных друзей на расклады",
                reply_markup = create_bonus_keyboard("paid", bonuses_paid)
            )


# Handler for initially viewing bonus cards (for returning to the list)
@router.callback_query(BonusCardCallbackFactory.filter(F.action == "view"))
async def view_bonus_card(call: types.CallbackQuery, callback_data: BonusCardCallbackFactory, bot: Bot):
    bonus_type = callback_data.bonus_type

    # Get current bonus status
    result = await execute_select(
        f"SELECT bonuses_{bonus_type} FROM users WHERE user_id = $1",
        (call.from_user.id,)
    )

    bonuses_status = result

    # Create updated keyboard
    updated_keyboard = create_bonus_keyboard(bonus_type, bonuses_status)

    # Update message with appropriate title
    if bonus_type == "li":
        title = "Бонусы за личные покупки и рефералов (тип 1):"
    else:
        title = "Бонусы за общее количество раскладов и рефералов (тип 2):"

    await call.message.edit_text(title, reply_markup = updated_keyboard)


# Confirmation dialog handler
@router.callback_query(BonusActionCallbackFactory.filter(F.action == "confirm"))
async def confirm_bonus_activation(call: types.CallbackQuery, callback_data: BonusActionCallbackFactory, bot: Bot):
    bonus_type = callback_data.type
    bonus_category = callback_data.cat  # "p" or "r"
    bonus_index = callback_data.idx

    # Determine proper bonus array and get the right message
    if bonus_type == "li":
        if bonus_category == "p":  # personal
            bonus_array = PERSONAL_LI_BONUSES
            actual_index = bonus_index
        else:  # referral (r)
            bonus_array = FRIEND_LI_BONUSES
            actual_index = bonus_index - 7
    else:  # paid
        if bonus_category == "p":  # personal
            bonus_array = PERSONAL_PAID_BONUSES
            actual_index = bonus_index
        else:  # referral (r)
            bonus_array = FRIEND_PAID_BONUSES
            actual_index = bonus_index - 7

    # Get confirmation message and create keyboard
    confirm_message = bonus_array[actual_index]["confirm_message"]
    confirm_keyboard = create_confirmation_keyboard(bonus_type, bonus_category, bonus_index)

    # Edit the message with confirmation
    await call.message.edit_text(confirm_message, reply_markup = confirm_keyboard)


# Actual bonus activation handler
@router.callback_query(BonusActionCallbackFactory.filter(F.action == "activate"))
async def handle_bonus_activation(call: types.CallbackQuery, callback_data: BonusActionCallbackFactory, bot: Bot):
    user_id = call.from_user.id
    bonus_type = callback_data.type
    bonus_category = callback_data.cat  # "p" or "r"
    bonus_index = callback_data.idx

    # Get the appropriate bonus array based on type and category
    if bonus_type == "li":
        if bonus_category == "p":  # personal
            bonus_array = PERSONAL_LI_BONUSES
            actual_index = bonus_index
        else:  # referral (r)
            bonus_array = FRIEND_LI_BONUSES
            actual_index = bonus_index - 7
    else:  # paid
        if bonus_category == "p":  # personal
            bonus_array = PERSONAL_PAID_BONUSES
            actual_index = bonus_index
        else:  # referral (r)
            bonus_array = FRIEND_PAID_BONUSES
            actual_index = bonus_index - 7

    # Get bonus name and function
    bonus_name = bonus_array[actual_index]["name"]
    bonus_function = bonus_array[actual_index]["function"]

    # Get current bonus status
    result = await execute_select(
        f"SELECT bonuses_{bonus_type} FROM users WHERE user_id = $1",
        (user_id,)
    )

    bonuses = list(result)

    # Verify the bonus is available
    if bonuses[bonus_index] != "2":
        await call.answer("Этот бонус недоступен или уже использован", show_alert = True)
        return

    # Mark the bonus as used
    bonuses[bonus_index] = "3"  # Mark as used
    new_bonuses = "".join(bonuses)

    # Update the database
    await execute_query(
        f"UPDATE users SET bonuses_{bonus_type} = $1 WHERE user_id = $2",
        (new_bonuses, user_id)
    )

    # Activate the bonus
    await activate_bonus(user_id, bot, bonus_type, bonus_name, bonus_function)

    # Update the keyboard with the new bonus status
    updated_keyboard = create_bonus_keyboard(bonus_type, new_bonuses)

    # Send confirmation message and update keyboard
    if bonus_type == "li":
        message = "Бонусы за личные покупки и рефералов (тип 1):"
    else:
        message = "Бонусы за общее количество раскладов и рефералов (тип 2):"

    await call.message.edit_text(
        message,
        reply_markup = updated_keyboard
    )


# Bonus activation handler functions
async def activate_weekly_spread(user_id, bot):
    """Activates weekly spread bonus for the user"""
    # Implementation for activating weekly spread
    await bot.send_message(
        user_id,
        "🔮 Ваш бонус «Расклад на неделю от Ли» активирован!\n\n"
        "Расклад будет доступен в вашем личном кабинете в течение 24 часов."
    )
    # Here you would add the actual logic to provide the weekly spread to the user
    # For example: await add_weekly_spread_to_user(user_id)


async def activate_monthly_spread(user_id, bot):
    """Activates monthly spread bonus for the user"""
    await bot.send_message(
        user_id,
        "🔮 Ваш бонус «Расклад на месяц от Ли» активирован!\n\n"
        "Расклад будет доступен в вашем личном кабинете в течение 24 часов."
    )
    # Actual implementation: await add_monthly_spread_to_user(user_id)


async def activate_week_premium(user_id, bot):
    """Activates week premium bonus for the user"""
    # Here you would update the user's premium status in the database

    await bot.send_message(
        user_id,
        "✨ Ваш бонус «Week премиум» активирован!\n\n"
        "Премиум статус успешно добавлен на 7 дней."
    )


async def activate_month_premium(user_id, bot):
    """Activates month premium bonus for the user"""
    # Update user's premium status for 30 days

    await bot.send_message(
        user_id,
        "✨ Ваш бонус «Month премиум» активирован!\n\n"
        "Премиум статус успешно добавлен на 30 дней."
    )


async def activate_discount_20(user_id, bot):
    """Activates 20% discount bonus for the user"""
    # Add discount coupon to user

    await bot.send_message(
        user_id,
        "💰 Ваш бонус «20% скидка» активирован!\n\n"
        "Скидка 20% будет автоматически применена к вашему следующему заказу в течение 30 дней."
    )


async def activate_discount_10(user_id, bot):
    """Activates 20% discount bonus for the user"""
    # Add discount coupon to user

    await bot.send_message(
        user_id,
        "💰 Ваш бонус «10% скидка» активирован!\n\n"
        "Скидка 10% будет автоматически применена к вашему следующему заказу в течение 30 дней."
    )


async def activate_discount_50(user_id, bot):
    """Activates 20% discount bonus for the user"""
    # Add discount coupon to user

    await bot.send_message(
        user_id,
        "💰 Ваш бонус «50% скидка» активирован!\n\n"
        "Скидка 50% будет автоматически применена к вашему следующему заказу в течение 30 дней."
    )


async def activate_free_question(user_id, bot):
    """Activates one free question bonus for the user"""
    # Add free question to user's account

    await bot.send_message(
        user_id,
        "❓ Ваш бонус «Free вопрос» активирован!\n\n"
        "1 бесплатный вопрос добавлен в ваш личный кабинет."
    )


async def activate_two_free_questions(user_id, bot):
    """Activates two free questions bonus for the user"""

    await bot.send_message(
        user_id,
        "❓ Ваш бонус «2 Free вопроса» активирован!\n\n"
        "2 бесплатных вопроса добавлены в ваш личный кабинет."
    )


async def activate_three_free_questions(user_id, bot):
    """Activates three free questions bonus for the user"""

    await bot.send_message(
        user_id,
        "❓ Ваш бонус «3 Free вопроса» активирован!\n\n"
        "3 бесплатных вопроса добавлены в ваш личный кабинет."
    )


async def activate_four_free_questions(user_id, bot):
    """Activates four free questions bonus for the user"""

    await bot.send_message(
        user_id,
        "❓ Ваш бонус «4 Free вопроса» активирован!\n\n"
        "4 бесплатных вопроса добавлены в ваш личный кабинет."
    )


# Bonus activation dispatcher
async def activate_bonus(user_id, bot, bonus_type, bonus_name, bonus_function):
    """Dispatches to the correct activation function based on the bonus function name"""
    function_map = {
        "activate_weekly_spread": activate_weekly_spread,
        "activate_monthly_spread": activate_monthly_spread,
        "activate_week_premium": activate_week_premium,
        "activate_month_premium": activate_month_premium,
        "activate_discount_10": activate_discount_10,
        "activate_discount_20": activate_discount_20,
        "activate_discount_50": activate_discount_50,
        "activate_free_question": activate_free_question,
        "activate_two_free_questions": activate_two_free_questions,
        "activate_three_free_questions": activate_three_free_questions,
        "activate_four_free_questions": activate_four_free_questions,
    }

    # Call the appropriate function
    if bonus_function in function_map:
        await function_map[bonus_function](user_id, bot)
    else:
        # Fallback message if function not found
        await bot.send_message(
            user_id,
            f"✅ Ваш бонус «{bonus_name}» активирован!\n\n"
            f"Бонус будет применен автоматически."
        )
