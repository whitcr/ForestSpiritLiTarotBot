from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# КНОПКИ ДЛЯ ВОЗВРАЩЕНИЯ В МЕНЮ
menu_return_buttons = [
    [InlineKeyboardButton(text = "Да!", callback_data = "menu_return")]
]
menu_return_keyboard = InlineKeyboardMarkup(inline_keyboard = menu_return_buttons)

# КНОПКИ ДЛЯ ДОПОВ
dop_card_keyboard_buttons = [
    [
        InlineKeyboardButton(text = 'Один доп', callback_data = "dop_card_1"),
        InlineKeyboardButton(text = 'Два допа', callback_data = "dop_card_2"),
        InlineKeyboardButton(text = 'Три допа', callback_data = "dop_card_3")
    ],
]

dop_card_keyboard = InlineKeyboardMarkup(inline_keyboard = dop_card_keyboard_buttons)

# КНОПКИ ДЛЯ РАСКЛАДА НА МЕСЯЦ И НЕДЕЛЮ
create_month_spread_buttons = [
    [InlineKeyboardButton(text = "Сделать расклад!", callback_data = "create_month_spread")]
]
create_month_spread_keyboard = InlineKeyboardMarkup(inline_keyboard = create_month_spread_buttons)

create_week_spread_buttons = [
    [InlineKeyboardButton(text = "Сделать расклад!", callback_data = "create_week_spread")]
]
create_week_spread_keyboard = InlineKeyboardMarkup(inline_keyboard = create_week_spread_buttons)

# КНОПКИ ДЛЯ ПРАКТИКИ
practice_menu_general_buttons = [
    [InlineKeyboardButton(text = "Интуиция", callback_data = "practice_menu_intuition")],
    [InlineKeyboardButton(text = "Таро", callback_data = "practice_menu_tarot")],
    [InlineKeyboardButton(text = "Медитация", callback_data = "practice_menu_meditation")],
    [InlineKeyboardButton(text = "Практики", callback_data = "practice_menu_practice")]
]
practice_menu_general_keyboard = InlineKeyboardMarkup(inline_keyboard = practice_menu_general_buttons)

practice_menu_tarot_buttons = [
    [
        InlineKeyboardButton(text = "Карта", callback_data = "practice_card"),
        InlineKeyboardButton(text = "Выбор карты", callback_data = "practice_choose_card")
    ],
    [
        InlineKeyboardButton(text = "Триплет", callback_data = "practice_triple"),
        InlineKeyboardButton(text = "Викторина", callback_data = "practice_quiz")
    ]
]
practice_menu_tarot_keyboard = InlineKeyboardMarkup(inline_keyboard = practice_menu_tarot_buttons)

practice_menu_intuition_buttons = [
    [
        InlineKeyboardButton(text = "Карта", callback_data = "practice_card"),
        InlineKeyboardButton(text = "Выбор карты", callback_data = "practice_choose_card")
    ],
    [InlineKeyboardButton(text = "Заливка", callback_data = "practice_zalivka")]
]
practice_menu_intuition_keyboard = InlineKeyboardMarkup(inline_keyboard = practice_menu_intuition_buttons)

practice_card_buttons = [
    [InlineKeyboardButton(text = "Ответ", callback_data = "practice_card_answer")]
]
practice_card_keyboard = InlineKeyboardMarkup(inline_keyboard = practice_card_buttons)

practice_zalivka_buttons = [
    [InlineKeyboardButton(text = "Ответ", callback_data = "practice_zalivka_answer")]
]
practice_zalivka_keyboard = InlineKeyboardMarkup(inline_keyboard = practice_zalivka_buttons)

practice_choose_card_buttons = [
    [InlineKeyboardButton(text = "Ответ", callback_data = "practice_choose_card_answer")]
]
practice_choose_card_keyboard = InlineKeyboardMarkup(inline_keyboard = practice_choose_card_buttons)

practice_general_menu_practices_buttons = [
    [
        InlineKeyboardButton(text = "Основы", callback_data = "practices_essentials"),
        InlineKeyboardButton(text = "Энергия", callback_data = "practices_energy")
    ],
    [
        InlineKeyboardButton(text = "Негатив", callback_data = "practices_negative"),
        InlineKeyboardButton(text = "Изобилие", callback_data = "practices_wealth")
    ],
    [
        InlineKeyboardButton(text = "Красота", callback_data = "practices_beauty"),
        InlineKeyboardButton(text = "Отношения", callback_data = "practices_relationship")
    ],
    [InlineKeyboardButton(text = "Разное", callback_data = "practices_other")]
]
practice_general_menu_practices_keyboard = InlineKeyboardMarkup(
    inline_keyboard = practice_general_menu_practices_buttons)

# КНОПКИ ДЛЯ РАССЫЛКИ
follow_daily_mailing_buttons = [
    [
        InlineKeyboardButton(text = "Луна", callback_data = "moon_follow_yes"),
        InlineKeyboardButton(text = "Расклад дня", callback_data = "day_card_follow_yes")
    ],
    [
        InlineKeyboardButton(text = "Расклад на неделю", callback_data = "week_card_follow_yes"),
        InlineKeyboardButton(text = "Расклад на месяц", callback_data = "month_card_follow_yes")
    ]
]
follow_daily_mailing_keyboard = InlineKeyboardMarkup(inline_keyboard = follow_daily_mailing_buttons)

moon_follow_no_buttons = [
    [InlineKeyboardButton(text = "Отписаться", callback_data = "moon_follow_no")]
]
moon_follow_no_keyboard = InlineKeyboardMarkup(inline_keyboard = moon_follow_no_buttons)

day_card_follow_no_buttons = [
    [InlineKeyboardButton(text = "Отписаться", callback_data = "day_card_follow_no")]
]
day_card_follow_no_keyboard = InlineKeyboardMarkup(inline_keyboard = day_card_follow_no_buttons)

week_card_follow_no_buttons = [
    [InlineKeyboardButton(text = "Отписаться", callback_data = "week_card_follow_no")]
]
week_card_follow_no_keyboard = InlineKeyboardMarkup(inline_keyboard = week_card_follow_no_buttons)

month_card_follow_no_buttons = [
    [InlineKeyboardButton(text = "Отписаться", callback_data = "month_card_follow_no")]
]
month_card_follow_no_keyboard = InlineKeyboardMarkup(inline_keyboard = month_card_follow_no_buttons)

# КНОПКИ ДЛЯ УЗНАТЬ АРКАНЫ
date_acranes_buttons = [
    [
        InlineKeyboardButton(text = "Аркан Личности", callback_data = "personal_date_arcane"),
        InlineKeyboardButton(text = "Аркан Судьбы", callback_data = "personal_fate_arcane")
    ]
]
date_acranes_keyboard = InlineKeyboardMarkup(inline_keyboard = date_acranes_buttons)

date_personal_arcane_buttons = [
    [InlineKeyboardButton(text = "Аркан Судьбы", callback_data = "personal_fate_arcane")]
]
date_personal_arcane_keyboard = InlineKeyboardMarkup(inline_keyboard = date_personal_arcane_buttons)

date_fate_arcane_buttons = [
    [InlineKeyboardButton(text = "Аркан Личности", callback_data = "personal_date_arcane")]
]
date_fate_arcane_keyboard = InlineKeyboardMarkup(inline_keyboard = date_fate_arcane_buttons)

# КНОПКИ ДЛЯ НАСТРОЙКИ ТРИПЛЕТОВ
set_triplet_buttons = [
    [
        InlineKeyboardButton(text = "Мегатриплет", callback_data = "set_mtriplet"),
        InlineKeyboardButton(text = "Супертриплет", callback_data = "set_striplet")
    ]
]
set_triplet_keyboard = InlineKeyboardMarkup(inline_keyboard = set_triplet_buttons)

# КНОПКИ ДЛЯ ПОСТИНГА
posting_buttons = [
    [
        InlineKeyboardButton(text = "Утро", callback_data = "morning_posting"),
        InlineKeyboardButton(text = "Вечер", callback_data = "evening_posting")
    ],
    [
        InlineKeyboardButton(text = "Мемы", callback_data = "meme_posting"),
        InlineKeyboardButton(text = "Триплет", callback_data = "triplet_posting")
    ],
    [
        InlineKeyboardButton(text = "Карта", callback_data = "card_posting"),
        InlineKeyboardButton(text = "История", callback_data = "history_posting")
    ]
]
posting_keyboard = InlineKeyboardMarkup(inline_keyboard = posting_buttons)

# ПОДПИСКА
follow_channel_buttons = [
    [InlineKeyboardButton(text = "Подключиться!", url = 'https://t.me/forestspirito')]
]
follow_channel_keyboard = InlineKeyboardMarkup(inline_keyboard = follow_channel_buttons)

# ПОДПИСКА КОНКУРС
follow_contest_buttons = [
    [InlineKeyboardButton(text = "Дыхание Леса", url = 'https://t.me/forestspirito')],
    [InlineKeyboardButton(text = "Познание Души", url = 'https://t.me/SoulMatrixTarot')],
    [InlineKeyboardButton(text = "С любовью, Алина", url = 'https://t.me/semirechenko')],
    [InlineKeyboardButton(text = "SisuritiTarot", url = 'https://t.me/sisuritiTarot')],
    [InlineKeyboardButton(text = "MaShineTarot", url = 'https://t.me/tarosmashey')],
    [InlineKeyboardButton(text = "Проверить подписки и участвовать", callback_data = "check_contest_follow")]
]
follow_contest_keyboard = InlineKeyboardMarkup(inline_keyboard = follow_contest_buttons)

# ПРИВАТНОЕ МЕНЮ
# menu_private_buttons = [
#     [ReplyKeyboardMarkup(text = 'Карта', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Триплет', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Расклад', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Расклад дня', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Узнать значение', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Колода', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Луна', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Совет Луны', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Практика', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Узнать аркан', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Рассылка', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Запись', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Медитация', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Мантра', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Аффирмация', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Заказать расклад', resize_keyboard = True)],
#     [ReplyKeyboardMarkup(text = 'Помощь', resize_keyboard = True)]
# ]
# menu_private_keyboard = ReplyKeyboardMarkup(keyboard = menu_private_buttons, resize_keyboard = True)
