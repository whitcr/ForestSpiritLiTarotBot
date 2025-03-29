from datetime import timedelta, datetime
from collections import defaultdict
import asyncio
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database import execute_query, execute_select_all


class StatisticsCache:
    def __init__(self, flush_interval: int = 60):
        self.cache = defaultdict(lambda: {
            'daily_count': 0,
            'weekly_count': 0,
            'monthly_count': 0,
            'total_count': 0
        })
        self.flush_interval = flush_interval
        self.last_flush = datetime.utcnow()
        self._lock = asyncio.Lock()
        self._flush_task = None
        self._is_running = False

    async def start_auto_flush(self):
        """Запускает авто-флаш в фоне, если ещё не запущено."""
        if not self._is_running:
            self._is_running = True
            self._flush_task = asyncio.create_task(self.auto_flush())

    async def increment(self, command: str):
        async with self._lock:
            counts = self.cache[command]
            counts['daily_count'] += 1
            counts['weekly_count'] += 1
            counts['monthly_count'] += 1
            counts['total_count'] += 1

    async def auto_flush(self):
        """Периодически сбрасывает данные в БД."""
        try:
            while True:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
        except asyncio.CancelledError:
            self._is_running = False
            raise
        except Exception as e:
            print(f"Error in auto_flush: {e}")
            self._is_running = False

    async def flush(self):
        async with self._lock:
            if not self.cache:
                return

            cache_copy = dict(self.cache)
            self.cache.clear()
            self.last_flush = datetime.utcnow()

        now = datetime.utcnow()
        today = now.date()
        week_start = today - timedelta(days = today.weekday())
        month_start = today.replace(day = 1)

        for command, counts in cache_copy.items():
            try:
                result = await execute_select_all(
                    """
                    SELECT daily_count, weekly_count, monthly_count, total_count,
                           last_daily_update, last_weekly_update, last_monthly_update
                    FROM statistics_handler 
                    WHERE command = $1
                    """,
                    (command,),
                )

                if result:
                    await execute_query(
                        """
                        UPDATE statistics_handler 
                        SET daily_count = daily_count + $1, 
                            weekly_count = weekly_count + $2, 
                            monthly_count = monthly_count + $3, 
                            total_count = total_count + $4, 
                            last_daily_update = $5, 
                            last_weekly_update = $6, 
                            last_monthly_update = $7
                        WHERE command = $8
                        """,
                        (counts['daily_count'], counts['weekly_count'],
                         counts['monthly_count'], counts['total_count'],
                         today, week_start, month_start, command)
                    )
                else:
                    await execute_query(
                        """
                        INSERT INTO statistics_handler 
                        (command, daily_count, weekly_count, monthly_count, total_count,
                         last_daily_update, last_weekly_update, last_monthly_update)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        (command, counts['daily_count'], counts['weekly_count'],
                         counts['monthly_count'], counts['total_count'],
                         today, week_start, month_start)
                    )
            except Exception as e:
                print(f"Error flushing command {command}: {e}")
                async with self._lock:
                    for k, v in counts.items():
                        self.cache[command][k] += v


CALLBACK_COMMAND_MAPPING = {
    'month_spread': 'Расклад на месяц',
    'admin_statistics_handlers': 'Статистика обработчиков',
    'get_my_profile': 'Мой профиль',
    'boosty_payment_': 'Оплата Boosty',
    'show_random_audio_sabliminals': 'Случайные сублиминалы',
    'day_card_follow': 'Подписка расклад дня',
    'get_def_gpt_:False': 'Обычная трактовка',
    'get_def_gpt_"True': 'Запрос на премиум трактовку',
    'approve_meanings': 'Подтвердить приобретение значения',
    'get_time_spread_meaning_': 'Получить значение расклада месяц/недели',
    'get_sub_': 'Меню подписки',
    'create_month_spread': 'Расклад на месяц',
    'get_meanings_': 'Получить значения',
    'select_sub_type_': 'Выбрать тип подписки',
    'get_user_statistics': 'Получить статистику пользователя',
    'meaning_raider_': 'Значение райдера',
    'get_meaning_premium': 'Премиум трактовка',
    'day_meaning_day_card_': 'Значение карты дня',
    'get_bonus_card': 'Получить бонусную карту',
    'month_card_follow': 'Подписка на расклад на месяц',
    'week_card_follow': 'Подписка на расклад на неделю',
    'change_situation': 'Изменить ситуацию',
    'today_spread': 'Расклад на сегодня',
    'create_week_premium_spread': 'Премиум расклад на неделю',
    'week_spread': 'Расклад на неделю',
    'get_day_spread_meaning_': 'Значение расклада дня',
    'create_week_spread': 'Расклад на неделю',
    'get_details': 'Получить детали',
    'show_practice_': 'Показать практику',
    'practices_': 'Практики',
    'get_sub_menu': 'Получить меню подписки',
    'sub_type_': 'Тип подписки',
    'get_practices_menu': 'Меню практик',
    'practice_menu_': 'Меню практик',
    'approve_payment_': 'Подтвердить оплату',
    'select_meanings_type': 'Выбрать тип значений',
    'menu_return': 'Возврат в меню',
    'admin_statistics_': 'Администраторская статистика',
    'get_support': 'Получить поддержку',
    'show_book_': 'Показать книгу',
    'send_payment_screenshot': 'Отправить скриншот оплаты',
    'start_quiz': 'Начать квиз',
    'tomorrow_spread': 'Расклад на завтра',
    'bonus_card_use_': 'Использование бонусной карты',
    'get_referral_url': 'Получить реферальную ссылку',
    'cancel_mailing': 'Отменить рассылку',
    'get_privacy': 'Получить приватность',
    'check_subscriptions': 'Проверить подписки',
    'invite_friends': 'Пригласить друзей',
    'practice_choose_card_': 'Практика Тройная Карта',
    'practice_card_': 'Практика Карта',
    'practice_quiz': 'Практика Викторина',
    'practice_history': 'Практика История',
    'practice_triple': 'Практика Триплет',
    'broadcast_': 'Рассылка всем',
    'admin_get_id': 'Получить ID администратора',
    'add_meanings_': 'Добавить значения',
    'add_coupon_': 'Добавить купон',
    'admin_coupons_': 'Добавить купон',
    'add_referrals_': 'Добавить рефералов',
    'admin_paid_spreads_': 'Добавление платных раскладов',
    'back_to_profile_': 'Вернуться в профиль',
    'moon_follow': 'Подписка на луну',
    'get_mailing': 'Меню рассылки',
    'get_dop_': 'Доп',
    'unknown_message': 'Неизвестное сообщение'
}

ALLOWED_COMMANDS = {
    "библиотека", "доп", "мантра", "мтриплет", "помощь",
    "стриплет", "колода", "карта", "значение", "расклад",
    "допы", "триплет", "саб", "мой профиль", 'карта', 'настройки', 'услуги',
    "расклад на день", "расклад на неделю",
    "расклад на завтра", "расклад на месяц", "практика"
}

COMMAND_ALIASES = {
    "расклад дня": "расклад на день",
    "расклад недели": "расклад на неделю",
    "расклад месяца": "расклад на месяц",
    "расклад завтра": "расклад на завтра",
    "значение": "узнать значение",
}

ALLOWED_COMMANDS = {cmd.lower() for cmd in ALLOWED_COMMANDS}


def get_command_name(callback_data: str) -> str:
    callback_data = callback_data.lower()

    for prefix, command_name in CALLBACK_COMMAND_MAPPING.items():
        if callback_data.startswith(prefix.lower()):
            return command_name

    for command in sorted(ALLOWED_COMMANDS, key = len, reverse = True):
        if callback_data.startswith(command):
            return command

    for alias, standard in COMMAND_ALIASES.items():
        if callback_data.startswith(alias):
            return standard

    return callback_data


def get_message_command(text: str) -> str:
    if not text:
        return "unknown_message"

    text = text.lower()

    for command in sorted(ALLOWED_COMMANDS, key = len, reverse = True):
        if text.startswith(command):
            return command

    first_word = text.split()[0]
    if first_word in ALLOWED_COMMANDS:
        return first_word

    return "unknown_message"


class HandlerStatisticsMiddleware(BaseMiddleware):
    def __init__(self, flush_interval: int = 60):
        self.stats_cache = StatisticsCache(flush_interval)
        self._auto_flush_started = False

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        if not self._auto_flush_started:
            await self.stats_cache.start_auto_flush()  # Запускаем и ждем запуска
            self._auto_flush_started = True

        if isinstance(event, Message):
            command = get_message_command(event.text) if event.text else "unknown_message"
        elif isinstance(event, CallbackQuery):
            command = get_command_name(event.data)
        else:
            command = 'unknown_event'

        asyncio.create_task(self.stats_cache.increment(command.lower()))

        return await handler(event, data)
