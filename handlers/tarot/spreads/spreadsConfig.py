from constants import FONT_L, FONT_M
from handlers.tarot.spreads.day.daySpread import tomorrow_spread, today_spread
from handlers.tarot.spreads.weekAndMonth.weekAndMonthDefault import get_month_week_spread_cb, get_month_week_spread

SPREADS = {
    "universe_sign_spread": {
        'name': {'Знак Вселенной'},
        "image": [
            ("Каким образом Вселенная дает знак?", FONT_M),
            ("Что хочет сказать Вселенная", FONT_M),
            ("На что мне обратить внимание?", FONT_M),
        ],
        'keywords': {'знак', 'знак вселенной', 'вселенной'},
        'cb_key': '1',
    },
    "relationship_spread": {
        'name': {'Отношения'},
        "image": [
            ("Его чувства к ней", FONT_L),
            ("Общие отношения", FONT_L),
            ("Ее чувства к нему", FONT_L),
        ],
        'keywords': {'отношения'},
        'cb_key': '2',
    },
    "his_feelings_spread": {
        'name': {'Его чувства'},
        "image": [
            ("Его чувства", FONT_L),
            ("Его мысли", FONT_L),
            ("Его действия", FONT_L),
        ],
        'keywords': {'чувства'},
        'cb_key': '3',
    },
    "health_spread": {
        'name': {'Здоровье'},
        "image": [
            ("Эмоции", FONT_L),
            ("Тело", FONT_L),
            ("Ум", FONT_L),
        ],
        'keywords': {'состояние', 'здоровье'},
        'cb_key': '4',
    },
    "study_spread": {
        'name': {'Учеба'},
        "image": [
            ("На что мне обратить внимание?", FONT_L),
            ("Нынешие дела в учебе", FONT_L),
            ("Как выйти в плюс", FONT_L),
        ],
        'keywords': {'учеба', 'учебу'},
        'cb_key': '5',
    },
    "time_spread": {
        'name': {'Время'},
        "image": [
            ("Прошлое", FONT_L),
            ("Настоящее", FONT_L),
            ("Будущее", FONT_L),
        ],
        'keywords': {'время', 'времени'},
        'cb_key': '6',
    },
    "finance_spread": {
        'name': {'Финансы'},
        "image": [
            ("На что мне обратить внимание?", FONT_L),
            ("Нынешие дела в финансах", FONT_L),
            ("Как выйти в плюс", FONT_L),
        ],
        'keywords': {'деньги', 'финансы'},
        'cb_key': '7',
    },
    "where_is_item_spread": {
        'name': {'Местоположение'},
        "image": [
            ("Характеристика места", FONT_M),
            ("Характеристика места", FONT_L),
            ("Характеристика места", FONT_M),
        ],
        'keywords': {'предмет', 'где', 'место'},
        'cb_key': '8',
    },
    "person_spread": {
        'name': {'Характер человека'},
        "image": [
            ("То, как себя показывает", FONT_L),
            ("То, кем является", FONT_L),
            ("То, что скрывает  ", FONT_L),
        ],
        'keywords': {'деньги', 'финансы'},
        'cb_key': '9',
    },
    "what_person_doing_spread": {
        'name': {'Занятие человека'},
        "image": [
            ("Характеристика дела", FONT_M),
            ("Характеристика дела", FONT_L),
            ("Характеристика дела", FONT_M),
        ],
        'keywords': {'что делает', 'дело'},
        'cb_key': '10',
    },
    "perspective_spread": {
        'name': {'Развитие'},
        "image": [
            ("Первый месяц", FONT_L),
            ("Второй месяц", FONT_L),
            ("Третий месяц", FONT_L),
        ],
        'keywords': {'развитие', 'перспектива'},
        'cb_key': '11',
    },
    "final_of_situation_spread": {
        'name': {'Итог ситуации'},
        "image": [
            ("Для других", FONT_L),
            ("Для меня", FONT_L),
            ("Какой урок понять", FONT_L),
        ],
        'keywords': {'итог', 'финал'},
        'cb_key': '12',
    },
    "today_spread": {
        'name': {'Сегодня'},
        'keywords': {'день', 'сегодня', 'дня'},
        'cb_key': '13',
        "func_cb": today_spread,
        "func": today_spread,
    },
    "tomorrow_spread": {
        'name': {'Завтра'},
        "keywords": {'завтра'},
        'cb_key': '14',
        "func_cb": tomorrow_spread,
        "func": tomorrow_spread,
    },
    "week_spread": {
        'name': {'Неделя'},
        "keywords": {'неделю', 'неделя', 'недели'},
        'cb_key': '15',
        "func_cb": get_month_week_spread_cb,
        "func": get_month_week_spread,
    },
    "month_spread": {
        'name': {'Месяц'},
        "keywords": {'месяц', 'месяца'},
        'cb_key': '16',
        "func_cb": get_month_week_spread_cb,
        "func": get_month_week_spread,
    },
}


async def get_name_by_cb_key(cb_key):
    for spread in SPREADS.values():
        if spread['cb_key'] == cb_key:
            return list(spread['name'])[0]
    return None


async def get_questions_by_name(name):
    for key, data in SPREADS.items():
        if name in data['name']:
            return [question for question, _ in data['image']]
    return []
