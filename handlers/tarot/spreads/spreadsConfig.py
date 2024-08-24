from constants import FONT_L, FONT_M
from handlers.tarot.spreads.day.daySpread import tomorrow_spread, today_spread
from handlers.tarot.spreads.weekAndMonth.weekAndMonthDefault import get_month_week_spread_cb, get_month_week_spread

SPREADS = {
    "universe_sign_spread": {
        'name': {'Знак Вселенной'},
        "image": [
            ("Каким образом она это делает?", FONT_M),
            ("Что хочет сказать Вселенная", FONT_M),
            ("На что обратить внимание?", FONT_M),
        ],
        'keywords': {'знак', 'знак вселенной', 'вселенной'},
    },
    "relationship_spread": {
        'name': {'Отношения'},
        "image": [
            ("Его чувства к ней", FONT_L),
            ("Общие отношения", FONT_L),
            ("Ее чувства к нему", FONT_L),
        ],
        'keywords': {'отношения'},
    },
    "his_feelings_spread": {
        'name': {'Его чувства'},
        "image": [
            ("Его чувства", FONT_L),
            ("Его мысли", FONT_L),
            ("Его действия", FONT_L),
        ],
        'keywords': {'чувства'},
    },
    "health_spread": {
        'name': {'Здоровье'},
        "image": [
            ("Эмоции", FONT_L),
            ("Тело", FONT_L),
            ("Ум", FONT_L),
        ],
        'keywords': {'состояние', 'здоровье'},
    },
    "study_spread": {
        'name': {'Учеба'},
        "image": [
            ("На что обратить внимание?", FONT_L),
            ("Нынешие дела в учебе", FONT_L),
            ("Как выйти в плюс", FONT_L),
        ],
        'keywords': {'учеба', 'учебу'},
    },
    "time_spread": {
        'name': {'Время'},
        "image": [
            ("Прошлое", FONT_L),
            ("Настоящее", FONT_L),
            ("Будущее", FONT_L),
        ],
        'keywords': {'время', 'времени'},
    },
    "finance_spread": {
        'name': {'Финансы'},
        "image": [
            ("На что обратить внимание?", FONT_L),
            ("Нынешие дела в финансах", FONT_L),
            ("Как выйти в плюс", FONT_L),
        ],
        'keywords': {'деньги', 'финансы'},
    },
    "where_is_item_spread": {
        'name': {'Местоположение'},
        "image": [
            ("", FONT_M),
            ("Характеристика места", FONT_L),
            ("", FONT_M),
        ],
        'keywords': {'предмет', 'где', 'место'},
    },
    "person_spread": {
        'name': {'Характер человека'},
        "image": [
            ("То, как себя показывает", FONT_L),
            ("То, кем является", FONT_L),
            ("То, что скрывает  ", FONT_L),
        ],
        'keywords': {'деньги', 'финансы'},
    },
    "what_person_doing_spread": {
        'name': {'Занятие человека'},
        "image": [
            ("", FONT_M),
            ("Характеристика дела", FONT_L),
            ("", FONT_M),
        ],
        'keywords': {'что делает', 'дело'},
    },
    "perspective_spread": {
        'name': {'Развитие'},
        "image": [
            ("Первый месяц", FONT_L),
            ("Второй месяц", FONT_L),
            ("Третий месяц", FONT_L),
        ],
        'keywords': {'развитие', 'перспектива'},
    },
    "final_of_situation_spread": {
        'name': {'Итог ситуации'},
        "image": [
            ("Для других", FONT_L),
            ("Для меня", FONT_L),
            ("Какой урок понять", FONT_L),
        ],
        'keywords': {'итог', 'финал'},
    },
    "today_spread": {
        'name': {'Сегодня'},
        'keywords': {'день', 'сегодня', 'дня'},
        "func_cb": today_spread,
        "func": today_spread,
    },
    "tomorrow_spread": {
        'name': {'Завтра'},
        "keywords": {'завтра'},
        "func_cb": tomorrow_spread,
        "func": tomorrow_spread,
    },
    "week_spread": {
        'name': {'Неделя'},
        "keywords": {'неделю', 'неделя', 'недели'},
        "func_cb": get_month_week_spread_cb,
        "func": get_month_week_spread,
    },
    "month_spread": {
        'name': {'Месяц'},
        "keywords": {'месяц', 'месяца'},
        "func_cb": get_month_week_spread_cb,
        "func": get_month_week_spread,
    },
}
