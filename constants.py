from PIL import ImageFont

SUBS_TYPE = {
    0: "Без подписки",
    1: "Шут",
    2: "Маг",
    3: "Жрица"
}

DAILY_LIMIT = 200

DECK_MAP = {
    'raider': 'Райдер-Уэйт',
    'wildwood': 'Дикий Лес',
    'saintdeath': 'Святая Смерть',
    'manara': 'Манара',
    'magicalforest': 'Магический Лес',
    'deviantmoon': 'Безумная Луна',
    'aftertarot': 'Таро Последствий',
    'ceccoli': 'Чекколи',
    'darkwood': 'Темный Лес',
    'decameron': 'Декамерон',
    'lenorman': 'Ленорман',
    'wildunknown': 'Дикое Неизвестное',
    'animalspirit': 'ДН Оракул',
    'vikaoracul': 'Викканский Оракул',
    'vikanimaloracul': 'Оракул Животных',
    'thothtarot': 'Таро Тота',
    'joytarot': 'Жизнерадостное Таро',
    # 'nightmare': 'Кошмар перед Рождеством' ,
}

CARDS_NAME_SYNONYMS = {
    'жрица': ['верховная жрица', 'папесса'],
    'иерофант': ['верховный жрец', 'жрец'],
    'суд': ['страшный суд'],
    'колесо фортуны': ['колесо', 'колесо фортуны'],

    'влюбленные': ['любовники', 'влюблённые'],
    'справедливость': ['правосудие'],
    'дьявол': ['сатана', 'демон'],

    'туз': ['1'],
    'двойка': ['2', 'два'],
    'тройка': ['3', 'три'],
    'четверка': ['4', 'четыре'],
    'пятерка': ['5', 'пять'],
    'шестерка': ['6', 'шесть'],
    'семерка': ['7', 'семь'],
    'восьмерка': ['8', 'восемь'],
    'девятка': ['9', 'девять'],
    'десятка': ['10', 'десять'],
    'паж': ['слуга'],
    'рыцарь': ['всадник', 'всадница'],
    'королева': ['дама'],
    'король': ['царь'],

    'чаш': ['кубки', 'воды', 'кубков', 'к', 'ч'],
    'пентаклей': ['монет', 'земли', 'денариев', 'п', 'з'],
    'мечей': ['воздуха', 'м', 'в'],
    'жезлов': ['огня', 'жезла', 'о', 'ж']
}

CARDS = ['шут', 'маг', 'жрица', 'верховная жрица', 'императрица', 'император', 'иерофант', 'жрец', 'влюбленные',
         'колесница', 'сила', 'отшельник', 'колесо фортуны', 'справедливость',
         'повешенный', 'смерть', 'умеренность', 'дьявол', 'башня', 'звезда', 'луна', 'солнце', 'суд', 'страшный суд',
         'мир', 'туз жезлов', 'двойка жезлов', 'тройка жезлов', 'четверка жезлов', 'пятерка жезлов', 'шестерка жезлов',
         'семерка жезлов', 'восьмерка жезлов', 'девятка жезлов', 'десятка жезлов', 'паж жезлов', 'рыцарь жезлов',
         'королева жезлов', 'король жезлов', 'туз чаш', 'двойка чаш', 'тройка чаш', 'четверка чаш', 'пятерка чаш',
         'шестерка чаш', 'семерка чаш', 'восьмерка чаш', 'девятка чаш', 'десятка чаш', 'паж чаш', 'рыцарь чаш',
         'королева чаш', 'король чаш', 'туз мечей', 'двойка мечей', 'тройка мечей', 'четверка мечей', 'пятерка мечей',
         'шестерка мечей', 'семерка мечей', 'восьмерка мечей', 'девятка мечей', 'десятка мечей', 'паж мечей',
         'рыцарь мечей', 'королева мечей', 'король мечей', 'туз пентаклей', 'двойка пентаклей', 'тройка пентаклей',
         'четверка пентаклей', 'пятерка пентаклей', 'шестерка пентаклей', 'семерка пентаклей', 'восьмерка пентаклей',
         'девятка пентаклей', 'десятка пентаклей', 'паж пентаклей', 'рыцарь пентаклей', 'королева пентаклей',
         'король пентаклей',
         ]

MEANINGS_BUTTONS = {
    "raider": {
        "text": ["Общее", "Подробнее", "Отношения", "Финансы", "Здоровье", "Личность", "Работа", "Перевернутое",
                 "Карта Дня", "Карта Совет", "Да или нет"],
        "callback_data": ["meaning_raider_general", "meaning_raider_more", "meaning_raider_relationship",
                          "meaning_raider_finance", "meaning_raider_health", "meaning_raider_person",
                          "meaning_raider_work", "meaning_raider_reverse", "meaning_raider_day",
                          "meaning_raider_advice", "meaning_raider_yesno"],
        "source": "https://www.taro.lv/"
    },
    "manara": {
        "text": ["Общее", "Перевернутое", "Астрология", "Состояние", "Отношения", "Секс", "Карта Дня", "Карта Совет"],
        "callback_data": ["meaning_manara_general", "meaning_manara_reverse", "meaning_manara_astrology",
                          "meaning_manara_person", "meaning_manara_relationship", "meaning_manara_sex",
                          "meaning_manara_day",
                          "meaning_manara_advice"],
        "source": "https://valiriya.ru/"
    },
    "deviantmoon": {
        "text": ["Общее", "Перевернутое", "Комментарии создателя"],
        "callback_data": ["meaning_deviantmoon_general", "meaning_deviantmoon_reverse", "meaning_deviantmoon_history"],
        "source": "https://booksnation.site/?book=1572816872"
    },
    "ceccoli": {
        "text": ["Общее", "Сюжет", "Отношения", "Работа", "Слабости", "Сны", "Карта совет", "Да или нет"],
        "callback_data": ["meaning_ceccoli_general", "meaning_ceccoli_plot", "meaning_ceccoli_relationship",
                          "meaning_ceccoli_job", "meaning_ceccoli_weakness",
                          "meaning_ceccoli_dreams", "meaning_ceccoli_advice", "meaning_ceccoli_yesno"],
        "source": "https://magiachisel.ru/"
    }
}

LOVE_SPREAD = ['любовь', 'отношения', 'на чувства', 'чувства']
YESNO_SPREAD = ['да или нет?', 'да или нет', 'да?', 'нет?', 'да нет', 'да/нет']
ADVICE_SPREAD = ['совет']

TOMORROW_SPREAD = ['на завтра', 'дня на завтра', 'завтрашнего дня', 'завтра']
TODAY_SPREAD = ['дня', 'на день']
AWARE_TODAY_SPREAD = ['угроза дня', 'угроза на день']
AWARE_TOMORROW_SPREAD = ['угроза завтра', 'угроза на завтра']
CONCLUSION_TODAY_SPREAD = ['итог дня', 'итог на день']
CONCLUSION_TOMORROW_SPREAD = ['итог завтра', 'итог на завтра']
ADVICE_TODAY_SPREAD = ['совет дня', 'совет на день']
ADVICE_TOMORROW_SPREAD = ['совет завтра', 'совет на завтра']

FONT_XXL = ImageFont.truetype("./images/tech/fonts/KTFJermilov-Solid.ttf", 50)
FONT_XL = ImageFont.truetype("./images/tech/fonts/KTFJermilov-Solid.ttf", 45)
FONT_L = ImageFont.truetype("./images/tech/fonts/KTFJermilov-Solid.ttf", 40)
FONT_M = ImageFont.truetype("./images/tech/fonts/KTFJermilov-Solid.ttf", 30)
FONT_S = ImageFont.truetype("./images/tech/fonts/KTFJermilov-Solid.ttf", 20)

P_FONT_S = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 50)
P_FONT_L = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 60)
P_FONT_XL = ImageFont.truetype("./images/tech/fonts/1246-font.otf", 100)
