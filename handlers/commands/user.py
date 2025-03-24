from aiogram import types, Router, Bot, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hlink
from datetime import datetime
import pytz
import pendulum

from constants import DECK_MAP, SUBS_TYPE
from database import execute_query, execute_select_all
from filters.subscriptions import SubscriptionLevel
from functions.cards.create import get_buffered_image
from functions.messages.messages import typing_animation_decorator
from functions.statistics.getUserStats import get_user_statistics
from keyboard import menu_private_keyboard, profile_keyboard
from middlewares.statsUser import UserStatisticsMiddleware

router = Router()
router.message.middleware(UserStatisticsMiddleware())
router.callback_query.middleware(UserStatisticsMiddleware())


@router.message(F.text.lower() == "меню")
async def get_menu(message: types.Message):
    if message.chat.type == "private":
        await message.reply(f'Вот тебе меню!',
                            reply_markup = menu_private_keyboard)


async def get_user_profile(user_id: int):
    query = """
    SELECT cards_type, subscription, subscription_date, moon_follow, day_card_follow, 
           week_card_follow, month_card_follow, total_count as interactions, boosted, referrals, paid_meanings,
           coupon_gold, coupon_silver, coupon_iron
    FROM users
    WHERE user_id = $1
    """
    return await execute_select_all(query, (user_id,))


@router.callback_query(F.data == "get_user_statistics", SubscriptionLevel(1), flags = {"use_user_statistics": True})
@typing_animation_decorator(initial_message = "Вычисляю статистику")
async def get_formatted_card_statistics(callback_query: types.CallbackQuery, bot):
    await callback_query.answer()
    image = await get_user_statistics(callback_query.from_user.id)
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text = "◀️ Назад в профиль", callback_data = "get_my_profile")

    await bot.edit_message_media(chat_id = callback_query.message.chat.id,
                                 message_id = callback_query.message.message_id,
                                 media = InputMediaPhoto(media = await get_buffered_image(image)),
                                 reply_markup = keyboard.as_markup())


@router.message(F.text.lower() == "мой профиль")
async def generate_profile_summary_cmd(message: types.Message, bot: Bot):
    if message.chat.type == "private":
        await generate_profile_summary(message, bot)
    else:
        await message.reply("Эта команда доступна только в личных сообщениях.")


@router.callback_query(F.data == "get_my_profile")
async def generate_profile_summary_cmd(call, bot: Bot):
    if call.message.chat.type == "private":
        await generate_profile_summary(call, bot)
    else:
        await call.message.reply("Эта команда доступна только в личных сообщениях.")


async def generate_profile_summary(message, bot: Bot):
    user_id = message.from_user.id
    cb = False

    if isinstance(message, CallbackQuery):
        message = message.message
        cb = True

    user_profile = await get_user_profile(user_id)

    profile_data = user_profile[0]

    deck_type = profile_data[0] if profile_data[0] else None
    subscription = profile_data[1]
    subscription_date = profile_data[2]
    day_follow = {
        "moon_follow": profile_data[3],
        "day_card_follow": profile_data[4],
        "week_card_follow": profile_data[5],
        "month_card_follow": profile_data[6],
    }
    interactions = profile_data[7]
    booster = profile_data[8]
    referrals_ids = profile_data[9]
    paid_meanings = profile_data[10]
    coupon_gold = profile_data[11]
    coupon_silver = profile_data[12]
    coupon_iron = profile_data[13]

    coupons = (f"{coupon_gold} золот{'ых' if coupon_gold != 1 else 'ой'}, "
               f"{coupon_silver} серебрян{'ых' if coupon_silver != 1 else 'ый'}, "
               f"{coupon_iron} железн{'ых' if coupon_iron != 1 else 'ый'}")

    deck_type = DECK_MAP[deck_type] if deck_type else "Не указано"
    subscription = SUBS_TYPE[subscription]['name'] if subscription else "Без подписки"

    subscription_date = subscription_date if subscription_date else "Без подписки"
    interactions = interactions if interactions else "Не указано"
    booster = 'Да' if booster else 'Нет'

    paid_meanings = paid_meanings if paid_meanings else "0"

    moon_follow = "Есть" if day_follow['moon_follow'] else 'Нет'
    day_card_follow = "Есть" if day_follow['day_card_follow'] else 'Нет'
    week_card_follow = "Есть" if day_follow['week_card_follow'] else 'Нет'
    month_card_follow = "Есть" if day_follow['month_card_follow'] else 'Нет'

    profile_text = (
        f"📋 <b>Ваш профиль</b>\n\n"
        f"<b>Колода:</b> {deck_type}\n"
        f"<b>Подписка:</b> {subscription}\n"
        f"<b>Конец подписки:</b> {subscription_date}\n"
        f"<b>Кол-во трактовок от Ли:</b> {paid_meanings}\n"
        f"<b>Рассылки:</b>\n"
        f"    🌙 Луна: {moon_follow}\n"
        f"    🌞 Расклад дня: {day_card_follow}\n"
        f"    📅 Расклад недели: {week_card_follow}\n"
        f"    📆 Расклад месяца: {month_card_follow}\n"
        f"<b>Купоны:</b> {coupons}\n"
        f"<b>Взаимодействий:</b> {interactions}\n"
        f"<b>Буст:</b> {booster}\n"
    )
    if cb:
        await message.delete()
        await message.answer(profile_text, reply_markup = profile_keyboard,
                             reply_to_message_id = message.reply_to_message.message_id)
    else:
        await message.answer(profile_text, reply_markup = profile_keyboard, reply_to_message_id = message.message_id)


@router.message(F.text.lower() == "услуги")
async def services(message: types.Message, bot: Bot):
    if message.chat.type == 'private':
        link = f"https://t.me/forestspiritottarotreviews"
        group = hlink("группе", link)
        link = f"https://t.me/kmorebi"
        wanderer = hlink("мне", link)
        await bot.send_message(message.chat.id,
                               text = f"— Вы можете ознакомиться с отзывами и услугами в этой {group} или напрямую по раскладам обратиться "
                                      f"ко {wanderer}\n\n")
    else:
        pass


@router.message(F.text.lower().endswith("библиотека"))
async def get_library(message: types.Message, bot: Bot):
    if message.chat.type == 'private':
        link = hlink('библиотеку', 'https://t.me/forestlibraryspirit')
        await bot.send_message(message.chat.id, text = f"— Приглашаем тебя в нашу {link}.")
    else:
        pass


@router.message(F.text.lower() == "удалить расклад дня")
async def delete_day_spread(message: types.Message):
    user_id = message.from_user.id
    new_date = datetime.now(pytz.timezone('Europe/Kiev'))
    date = new_date.strftime("%d.%m")
    await execute_query("delete FROM spreads_day WHERE user_id = $1 and date = $2", (user_id, date,))
    await message.reply("Ваш расклад дня удален, но даже не найдетесь, что он не проиграется.")


@router.message(F.text.lower() == "удалить расклад на завтра")
async def delete_tomorrow_spread(message: types.Message):
    user_id = message.from_user.id
    tomorrow = pendulum.tomorrow('Europe/Kiev').format('DD.MM')
    await execute_query("delete FROM spreads_day WHERE user_id = $1 and date = $2", (user_id, tomorrow))
    await message.reply("Ваш расклад на завтра удален, но даже не найдетесь, что он не проиграется.")
