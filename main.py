import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import load_config

config = load_config()
API_TOKEN = config.tg_bot.token
ADMIN_ID = config.tg_bot.admin_ids[0]

logger = logging.getLogger(__name__)

bot: Bot = Bot(token = API_TOKEN, parse_mode = "HTML")
dp: Dispatcher = Dispatcher()


# @dp.error()
async def handle_error(exception: Exception) -> None:
    try:
        await bot.send_message(ADMIN_ID, f"Error: {exception}")
    except Exception as e:
        logger.exception(f"An error occurred while sending error message: {e}")


async def on_startup() -> None:
    try:

        from functions.temporaryStore import delete_expired_data
        # asyncio.create_task(delete_expired_data())
        logger.info('Starting bot')
        await bot.send_message(ADMIN_ID, "Bot started!")
    except Exception as e:
        logger.exception(f"An error occurred during bot startup: {e}")


async def on_shutdown() -> None:
    try:
        logger.info('Stopping bot')
        await bot.send_message(ADMIN_ID, "Bot stopped!")
    except Exception as e:
        logger.exception(f"An error occurred during bot shutdown: {e}")


async def main() -> None:
    logging.basicConfig(
        level = logging.INFO,
        format = '%(filename)s:%(lineno)d #%(levelname)-8s '
                 '[%(asctime)s] - %(name)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    from handlers.tarot import getCard, getDeck, getDops
    from events import addedToGroup, bannedByUser
    # from middlewares.baseMiddleware import CheckingSubscription
    from handlers.tarot import getMeaning, getMeaningCb
    from handlers.tarot.spreads import getWeekMonthSpread, getDaySpread, getSpreads, experimentalSpreads
    from handlers.numerology import getDateArcanes
    # Include routers for different functionalities

    from handlers.tarot.questions import getQuestions
    dp.include_routers(getCard.router, addedToGroup.router, bannedByUser.router, getDeck.router, getMeaning.router,
                       getMeaningCb.router, experimentalSpreads.router, getWeekMonthSpread.router, getDaySpread.router,
                       getQuestions.router, getDateArcanes.router, getSpreads.router, getDops.router)

    # Add middleware to handle callback queries
    # dp.callback_query.outer_middleware(CheckingSubscription())
    from middlewares.throttling import ThrottlingMiddleware
    dp.update.middleware(ThrottlingMiddleware())
    # Register functions to run on startup and shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling the bot
    await bot.delete_webhook(drop_pending_updates = True)
    await dp.start_polling(bot, skip_updates = True)


if __name__ == "__main__":
    asyncio.run(main())
