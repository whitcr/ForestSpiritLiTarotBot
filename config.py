import os
from dataclasses import dataclass
from dotenv import load_dotenv

# load_dotenv()


@dataclass
class DatabaseConfig:
    database: str
    db_host: str
    db_user: str
    db_password: str


@dataclass
class WebhookConfig:
    webhook_path: str
    base_webhook_url: str
    webhook_host: str
    webhook_port: int


@dataclass
class TgBot:
    token: str
    bot_id: int
    admin_id: int
    channel_id: int
    chat_id: int
    channel_username: str


@dataclass
class Config:
    tg_bot: TgBot
    webhook: WebhookConfig
    db: DatabaseConfig


def load_config() -> Config:
    return Config(
        tg_bot = TgBot(
            token = os.environ['API_TOKEN'],
            admin_id = int(os.environ.get('ADMIN_ID', '0')),
            channel_id = int(os.environ.get('CHANNEL_ID', '0')),
            bot_id = int(os.environ.get('BOT_ID', '0')),
            chat_id = int(os.environ.get('CHAT_ID', '0')),
            channel_username = os.environ.get('CHANNEL_USERNAME', '0')
        ),
        webhook = WebhookConfig(
            webhook_path = os.environ.get('WEBHOOK_PATH', ''),
            base_webhook_url = os.environ.get('BASE_WEBHOOK_URL', ''),
            webhook_host = os.environ.get('HOST', '0.0.0.0'),
            webhook_port = os.environ.get('PORT', default = 8000)
        ),
        db = DatabaseConfig(
            database = os.environ.get('NAME_DB', ''),
            db_host = os.environ.get('HOST_DB', ''),
            db_user = os.environ.get('USER_DB', ''),
            db_password = os.environ.get('PASSWORD_DB', '')
        )
    )
