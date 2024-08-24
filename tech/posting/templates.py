from PIL import Image
from PIL import ImageFilter

from functions.cards.create import get_path_background


async def get_post_template():
    background_path = await get_path_background()

    color = Image.open('./cards/tech/design_posts/backcolor.png').convert("RGBA")
    front = Image.open('./cards/tech/design_posts/front.png').convert("RGBA")

    background = Image.open(background_path).convert("RGBA")
    background = background.resize((1920, 1080))

    background = background.filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, background, alpha = .2)
    image.paste(front, (0, 0), front)

    return image


async def notify_week_spread(bot, channel_id):
    message = (f" — Пишем <b>'расклад на неделю'</b> в комментариях и узнаем, чего опасаться и чего ждать в следующие "
               f"семь дней. Чем больше реакций, тем лучше карты <3")
    await bot.send_message(CHANNEL_ID, message)
