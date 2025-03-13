import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from config import load_config
from handlers.commands import user
from middlewares.logger import LoggingMiddleware
from middlewares.statsHandler import HandlerStatisticsMiddleware
from routers import setup_routers

from tech.schedule.setSchedule import schedule
from functions.store.temporaryStore import delete_expired_data
from middlewares.coupons import CouponMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.subscription import CheckingSubscription

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, admin_id, channel_id, logger_chat) -> None:
    try:
        _delete_data_task = asyncio.create_task(delete_expired_data())
        _schedule_task = asyncio.create_task(schedule(bot, channel_id, admin_id))
        logger.info('Starting bot')
        await bot.send_message(logger_chat, "Bot started!")
    except Exception as e:
        logger.exception(f"An error occurred during bot startup: {e}")


async def on_shutdown(bot: Bot, logger_chat) -> None:
    try:
        await bot.delete_webhook(drop_pending_updates = True)
        logger.info('Stopping bot')
        await bot.send_message(logger_chat, "Bot stopped!")
    except Exception as e:
        logger.exception(f"An error occurred during bot shutdown: {e}")


def main() -> None:
    config = load_config()
    api_token = config.tg_bot.token
    admin_id = config.tg_bot.admin_id
    channel_id = config.tg_bot.channel_id
    logger_chat = config.tg_bot.logger_chat

    bot = Bot(token = api_token, default = DefaultBotProperties(parse_mode = ParseMode.HTML))
    dp = Dispatcher()

    logging.basicConfig(
        level = logging.INFO,
        format = '%(filename)s:%(lineno)d #%(levelname)-8s '
                 '[%(asctime)s] - %(name)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    router = setup_routers()
    dp.include_router(router)

    dp.message.middleware(CheckingSubscription())
    dp.callback_query.middleware(CheckingSubscription())

    dp.include_router(user.router)

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    stats_middleware = HandlerStatisticsMiddleware(flush_interval = 60)

    dp.message.outer_middleware(stats_middleware)
    dp.callback_query.outer_middleware(stats_middleware)

    dp.update.outer_middleware(CouponMiddleware())

    dp.update.outer_middleware(LoggingMiddleware())

    dp.workflow_data.update(
        {'admin_id': admin_id, 'channel_id': channel_id, 'api_token': api_token, 'logger_chat': logger_chat})

    if config.webhook.webhook_path:

        webhook_path = config.webhook.webhook_path
        base_webhook_url = config.webhook.base_webhook_url
        webhook_url = f"{base_webhook_url}{webhook_path}"
        host, port = config.webhook.webhook_host, config.webhook.webhook_port

        # https://habr.com/ru/articles/655965/

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await on_startup(bot, admin_id, channel_id)
            await bot.set_webhook(url = webhook_url,
                                  allowed_updates = dp.resolve_used_update_types(),
                                  drop_pending_updates = True)
            yield
            await on_shutdown(bot, admin_id)

            # await bot.session.close()

        app = FastAPI(lifespan = lifespan)

        @app.post(webhook_path)
        async def bot_webhook(request: Request):
            update = Update.model_validate(await request.json(), context = {"bot": bot})
            await dp.feed_update(bot, update)

        uvicorn.run(app, host = host, port = port)

    else:
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        asyncio.run(dp.start_polling(bot, skip_updates = True,
                                     allowed_updates = dp.resolve_used_update_types()))


if __name__ == "__main__":
    main()
