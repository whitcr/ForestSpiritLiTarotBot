from aiogram import types, F, Router, Bot
from aiogram.utils.media_group import MediaGroupBuilder

from database import execute_select, execute_query
from filters.baseFilters import IsAdmin

router = Router()


@router.callback_query(IsAdmin(), F.data == 'meme_posting')
async def get_meme_posting(call: types.CallbackQuery, bot: Bot, channel_id):
    await call.answer()
    await posting_memes(bot, channel_id)


async def posting_memes(bot, channel_id):
    try:
        media_group = MediaGroupBuilder()
        memes = await execute_select("SELECT number, memes FROM memes ORDER BY number LIMIT 4")

        for number, meme in memes:
            media_group.add_photo(media = meme)
            await execute_query("DELETE FROM memes WHERE number = $1", (number,))

        await bot.send_media_group(channel_id, media = media_group.build())
    except Exception as e:
        pass
