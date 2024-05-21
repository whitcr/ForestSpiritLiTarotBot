import os

from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


def load_config() -> Config:
    return Config(
        tg_bot = TgBot(
            token = os.environ['API_TOKEN'],
            admin_ids = [int(os.environ.get('ADMIN_ID', '0'))]
        ),
        db = DatabaseConfig(
            database = os.environ.get('NAME_DB', ''),
            db_host = os.environ.get('HOST_DB', ''),
            db_user = os.environ.get('USER_DB', ''),
            db_password = os.environ.get('PASSWORD_DB', '')
        )
    )


BOT_ID = 5519486207
ADMIN_ID = 504890623
CHANNEL_ID = -1001722903543
CHAT_ID = -1001894916266

CHANNEL = "@forestspirito"
