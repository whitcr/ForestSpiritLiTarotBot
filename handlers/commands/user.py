from aiogram import types, Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hlink
from datetime import datetime
import pytz
import pendulum

from constants import DECK_MAP, SUBS_TYPE
from database import execute_query, execute_select_all
from events.user.referrals import get_referrals
from functions.cards.create import get_buffered_image
from functions.messages.messages import get_reply_message, get_chat_id, typing_animation_decorator
from functions.statistics.getUserStats import get_user_statistics
from keyboard import menu_private_keyboard, profile_keyboard

router = Router()


@router.message(CommandStart())
async def start(message: types.Message, bot: Bot):
    command_params = message.text

    if "ref_" in command_params:
        await get_referrals(bot, message, command_params)

    if message.chat.type == "private":
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.reply(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?',
                            reply_markup = menu_private_keyboard)
    else:
        await get_help(message)


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


@router.callback_query(F.data == "get_user_statistics")
@typing_animation_decorator(initial_message = "Вычисляю статистику")
async def get_formatted_card_statistics(callback_query: types.CallbackQuery, bot):
    await callback_query.answer()
    image = await get_user_statistics(callback_query.from_user.id)

    await bot.send_photo(chat_id = await get_chat_id(callback_query), photo = await get_buffered_image(image),
                         reply_to_message_id = await get_reply_message(callback_query))


@router.message(F.text.lower() == "мой профиль")
async def generate_profile_summary(message: types.Message):
    user_id = message.from_user.id
    user_profile = await get_user_profile(user_id)
    profile_data = user_profile[0]

    deck_type = profile_data[0]
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
    referrals = profile_data[9]
    paid_meanings = profile_data[10]
    coupon_gold = profile_data[11]
    coupon_silver = profile_data[12]
    coupon_iron = profile_data[13]

    coupons = (f"{coupon_gold} золот{'ых' if coupon_gold != 1 else 'ой'}, "
               f"{coupon_silver} серебрян{'ых' if coupon_silver != 1 else 'ый'}, "
               f"{coupon_iron} железн{'ых' if coupon_iron != 1 else 'ый '}")

    deck_type = DECK_MAP[deck_type] if deck_type else "Не указано"
    subscription = SUBS_TYPE[subscription] if subscription else "Без подписки"

    subscription_date = subscription_date if subscription_date else "Без подписки"
    interactions = interactions if interactions else "Не указано"
    booster = 'Да' if booster else 'Нет'
    referrals = referrals if referrals else "Нет приглашенных"
    paid_meanings = paid_meanings if paid_meanings else "0"

    # Проверка на наличие значений для day_follow и установка текстов по умолчанию
    moon_follow = "Есть" if day_follow['moon_follow'] else 'Нет'
    day_card_follow = "Есть" if day_follow['day_card_follow'] else 'Нет'
    week_card_follow = "Есть" if day_follow['week_card_follow'] else 'Нет'
    month_card_follow = "Есть" if day_follow['month_card_follow'] else 'Нет'

    # Формирование текста профиля
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
        f"<b>Купоны:</b>{coupons}\n"
        f"<b>Взаимодействий:</b> {interactions}\n"
        f"<b>Буст:</b> {booster}\n"
        f"<b>Приглашенные:</b>  {referrals}\n"
    )

    await message.answer(profile_text, reply_markup = profile_keyboard, reply_to_message_id = message.message_id)


@router.message(F.text.lower() == "помощь")
async def get_help(message: types.Message):
    if message.chat.type == "private":
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.answer(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?',
                             reply_markup = menu_private_keyboard)
    else:
        text = hlink('—', 'https://telegra.ph/Lesnoj-Duh-Li-10-10')
        await message.answer(f'{text} Тебя приветствует <b>Лесной Дух</b>. Чего желаешь?')


@router.message(F.text.lower() == "заказать расклад")
async def services(message: types.Message, bot: Bot):
    if message.chat.type == 'private':
        link = f"https://t.me/forestspiritoo"
        group = hlink("группе", link)
        link = f"https://t.me/forestspiritoo"
        wanderer = hlink("Страннику", link)
        link = f"https://t.me/forestspiritoo/54"
        love_spread = hlink("Все о любви, его чувствах и намерениях", link)
        link = f"https://t.me/forestspiritoo/56"
        self_spread = hlink("Понимая себя, мы открываем совершенно иной мир", link)
        link = f"https://t.me/forestspiritoo/57"
        money_spread = hlink("Как улучшть свои финансы и что принесет мне этот путь?", link)
        await bot.send_message(message.chat.id,
                               text = f"— Вы можете ознакомиться с раскладами и иными услугами в этой {group} или напрямую обратиться "
                                      f"к {wanderer}\n\n"
                                      f"<b>ПОПУЛЯРНЫЕ РАСКЛАДЫ:</b>\n\n"
                                      f"{love_spread}\n\n"
                                      f"{self_spread}\n\n"
                                      f"{money_spread}\n\n")
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
    newdate = datetime.now(pytz.timezone('Europe/Kiev'))
    date = newdate.strftime("%d.%m")
    await execute_query("delete FROM spreads_day WHERE user_id = '{}' and date = '{}'", (user_id, date,))
    await message.reply("Ваш расклад дня удален, но даже не найдетесь, что он не проиграется.")


@router.message(F.text.lower() == "удалить расклад на завтра")
async def delete_tomorrow_spread(message: types.Message):
    user_id = message.from_user.id
    tomorrow = pendulum.tomorrow('Europe/Kiev').format('DD.MM')
    await execute_query("delete FROM spreads_day WHERE user_id = '{}' and date = '{}'", (user_id, tomorrow))
    await message.reply("Ваш расклад на завтра удален, но даже не найдетесь, что он не проиграется.")


@router.message(F.text.lower() == "!айди")
async def test(message: types.Message, bot: Bot, admin_id):
    await bot.send_message(admin_id, f"{message.from_user.id}")


@router.message(F.text.lower() == "айди")
async def get_id(message: types.Message, bot: Bot, admin_id):
    await bot.send_message(admin_id,
                           text = f"{message.from_user.id} - {message.from_user.first_name}")
