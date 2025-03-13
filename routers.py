from aiogram import Router

from events.group import addedToGroup
from events.user import bannedByUser, referrals
from handlers.audio import audio
from handlers.commands import owner, user, support
from handlers.tarot.spreads import getSpreads
from handlers.tarot.spreads.meaningSpreads import getMeaningSpread
from handlers.tarot.spreads.weekAndMonth import weekAndMonthDefault, weekAndMonthPremium
from handlers.tarot.spreads.day import daySpread
from handlers.tarot.spreads.day import meaningDaySpread
from events.channel import givedBoost
from events.subscriptions import getInvoice
from handlers.numerology import date
from handlers.tarot.cards import card, chooseDeck
from handlers.tarot.dops import dopCard
from handlers.tarot.meaningCards import meaning, meaningCb
from handlers.tarot.questions import questions
from handlers.tarot.spreads.experimental import experimental
from middlewares.statsUser import UserStatisticsMiddleware
from tech.mailing import settings
from tech.creating import menuCreate
from functions.bonuses import createBonusCard
from functions.bonuses import giveBonuses


def setup_routers():
    router = Router()

    card.router.message.middleware(UserStatisticsMiddleware())

    experimental.router.message.middleware(UserStatisticsMiddleware())
    experimental.router.callback_query.middleware(UserStatisticsMiddleware())

    weekAndMonthDefault.router.message.middleware(UserStatisticsMiddleware())
    weekAndMonthDefault.router.callback_query.middleware(UserStatisticsMiddleware())

    daySpread.router.message.middleware(UserStatisticsMiddleware())
    daySpread.router.callback_query.middleware(UserStatisticsMiddleware())

    getSpreads.router.message.middleware(UserStatisticsMiddleware())
    getSpreads.router.callback_query.middleware(UserStatisticsMiddleware())

    dopCard.router.message.middleware(UserStatisticsMiddleware())
    dopCard.router.callback_query.middleware(UserStatisticsMiddleware())

    chooseDeck.router.message.middleware(UserStatisticsMiddleware())
    chooseDeck.router.callback_query.middleware(UserStatisticsMiddleware())

    meaning.router.message.middleware(UserStatisticsMiddleware())
    meaning.router.callback_query.middleware(UserStatisticsMiddleware())

    meaningCb.router.message.middleware(UserStatisticsMiddleware())
    meaningCb.router.callback_query.middleware(UserStatisticsMiddleware())

    getMeaningSpread.router.message.middleware(UserStatisticsMiddleware())
    getMeaningSpread.router.callback_query.middleware(UserStatisticsMiddleware())

    router.include_routers(card.router, addedToGroup.router, bannedByUser.router, chooseDeck.router, meaning.router,
                           meaningCb.router, experimental.router, weekAndMonthDefault.router, daySpread.router,
                           questions.router, date.router, getSpreads.router, dopCard.router,
                           getMeaningSpread.router, meaningDaySpread.router, givedBoost.router,
                           getInvoice.router, settings.router, menuCreate.router, weekAndMonthPremium.router,
                           owner.router, user.router, referrals.router, audio.router, createBonusCard.router,
                           giveBonuses.router, support.router)

    return router
