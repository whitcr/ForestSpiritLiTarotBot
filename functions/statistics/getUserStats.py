import json

from constants import FONT_M, FONT_S, FONT_L
from database import execute_select_all
from collections import Counter

import numpy as np

from functions.cards.create import get_colors_background, get_gradient_3d,\
    get_path_background, get_path_cards

from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw


async def get_user_statistics(user_id):
    result = await execute_select_all(
        """
        SELECT daily_stats_cards, weekly_stats_cards, monthly_stats_cards, total_stats_cards, 
               last_daily_update_cards, last_weekly_update_cards, last_monthly_update_cards
        FROM users
        WHERE user_id = $1
        LIMIT 1
        """,
        (user_id,)
    )

    (daily_stats_json, weekly_stats_json, monthly_stats_json, total_stats_json,
     last_daily_update, last_weekly_update, last_monthly_update) = result[0]
    daily_stats = json.loads(daily_stats_json) if daily_stats_json else {}
    weekly_stats = json.loads(weekly_stats_json) if weekly_stats_json else {}
    monthly_stats = json.loads(monthly_stats_json) if monthly_stats_json else {}
    total_stats = json.loads(total_stats_json) if total_stats_json else {}

    stats = {
        'daily_stats': daily_stats,
        'weekly_stats': weekly_stats,
        'monthly_stats': monthly_stats,
        'total_stats': total_stats
    }

    result = await execute_select_all(
        """
        SELECT daily_count, weekly_count, monthly_count, total_count,
               last_daily_update, last_weekly_update, last_monthly_update
        FROM users
        WHERE user_id = $1
        """,
        (user_id,)
    )

    (
        daily_count, weekly_count, monthly_count, total_count, last_daily_update, last_weekly_update,
        last_monthly_update) =\
        result[0]

    stats_count = {
        'daily_count': daily_count,
        'weekly_count': weekly_count,
        'monthly_count': monthly_count,
        'total_count': total_count
    }

    image = await format_card_statistics(
        stats['daily_stats'], stats['weekly_stats'], stats['monthly_stats'], stats['total_stats'], stats_count
    )

    return image


async def format_card_statistics(daily_stats, weekly_stats, monthly_stats, total_stats, stats_count):
    async def format_stats_section(stats):
        card_counter = Counter(stats)
        most_common = card_counter.most_common()
        most_popular = most_common[:3]
        least_popular = most_common[-3:]

        most_popular = [(await get_path_cards('raider', card), count) for card, count in most_popular]
        least_popular = [(await get_path_cards('raider', card), count) for card, count in least_popular]

        return most_popular, least_popular

    async def get_section_paths(stats):
        return await format_stats_section(stats)

    daily_section_paths = await get_section_paths(daily_stats)
    weekly_section_paths = await get_section_paths(weekly_stats)
    monthly_section_paths = await get_section_paths(monthly_stats)
    total_section_paths = await get_section_paths(total_stats)

    choice = 'raider'

    col1, col2 = await get_colors_background(choice)

    cards = np.random.randint(col1, col2, size = 6)
    array = get_gradient_3d(1920, 1080, (cards[0], cards[1], cards[2]), (cards[3], cards[4], cards[5]),
                            (True, False, True))
    color = Image.fromarray(np.uint8(array))

    # Combine all paths into a single list
    card_paths = [
        path for section in (
            daily_section_paths,
            weekly_section_paths,
            monthly_section_paths,
            total_section_paths
        ) for path, _ in section[0] + section[1]
    ]

    card_counts = [
        count for section in (
            daily_section_paths,
            weekly_section_paths,
            monthly_section_paths,
            total_section_paths
        ) for _, count in section[0] + section[1]
    ]

    background_path = await get_path_background()
    background = Image.open(background_path).resize((1920, 1080)).filter(ImageFilter.GaussianBlur(radius = 3))
    image = Image.blend(color, background, alpha = 0.4)

    images = []

    for i, path in enumerate(card_paths):
        card = Image.open(path).convert("RGBA")
        card = card.resize((128, 214))
        images.append(card)

    draw_text = ImageDraw.Draw(image)

    draw_text.text((250, 25), 'За день', fill = 'white', font = FONT_M)

    image.paste(images[0], (65, 114))
    image.paste(images[1], ((65 + 128 + 40), 114))
    image.paste(images[2], ((65 + 2 * 128 + 2 * 40), 114))

    draw_text.text((110, 75), str(card_counts[0]), fill = 'white', font = FONT_S)
    draw_text.text((280, 75), str(card_counts[1]), fill = 'white', font = FONT_S)
    draw_text.text((455, 75), str(card_counts[2]), fill = 'white', font = FONT_S)

    image.paste(images[3].resize((102, 166)), (107, 362))
    image.paste(images[4].resize((102, 166)), ((107 + 102 + 40), 362))
    image.paste(images[5].resize((102, 166)), ((107 + 2 * 102 + 2 * 40), 362))

    draw_text.text((140, 328), str(card_counts[3]), fill = 'white', font = FONT_S)
    draw_text.text((278, 328), str(card_counts[4]), fill = 'white', font = FONT_S)
    draw_text.text((430, 328), str(card_counts[5]), fill = 'white', font = FONT_S)

    draw_text.text((230, 554), 'За неделю', fill = 'white', font = FONT_M)

    image.paste(images[6], (65, 643))
    image.paste(images[7], ((65 + 128 + 40), 643))
    image.paste(images[8], ((65 + 2 * 128 + 2 * 40), 643))

    draw_text.text((110, 604), str(card_counts[6]), fill = 'white', font = FONT_S)
    draw_text.text((280, 604), str(card_counts[7]), fill = 'white', font = FONT_S)
    draw_text.text((455, 604), str(card_counts[8]), fill = 'white', font = FONT_S)

    image.paste(images[9].resize((102, 166)), (107, 892))
    image.paste(images[10].resize((102, 166)), ((107 + 102 + 40), 892))
    image.paste(images[11].resize((102, 166)), ((107 + 2 * 102 + 2 * 40), 892))

    draw_text.text((140, 856), str(card_counts[9]), fill = 'white', font = FONT_S)
    draw_text.text((278, 856), str(card_counts[10]), fill = 'white', font = FONT_S)
    draw_text.text((430, 856), str(card_counts[11]), fill = 'white', font = FONT_S)

    draw_text.text((844, 554), 'За месяц', fill = 'white', font = FONT_M)

    image.paste(images[6], (671, 643))
    image.paste(images[7], ((671 + 128 + 40), 643))
    image.paste(images[8], ((671 + 2 * 128 + 2 * 40), 643))

    draw_text.text((710, 604), str(card_counts[6]), fill = 'white', font = FONT_S)
    draw_text.text((883, 604), str(card_counts[7]), fill = 'white', font = FONT_S)
    draw_text.text((1060, 604), str(card_counts[8]), fill = 'white', font = FONT_S)

    image.paste(images[9].resize((102, 166)), (713, 892))
    image.paste(images[10].resize((102, 166)), ((713 + 102 + 40), 892))
    image.paste(images[11].resize((102, 166)), ((713 + 2 * 102 + 2 * 40), 892))

    draw_text.text((750, 856), str(card_counts[9]), fill = 'white', font = FONT_S)
    draw_text.text((895, 856), str(card_counts[10]), fill = 'white', font = FONT_S)
    draw_text.text((1035, 856), str(card_counts[11]), fill = 'white', font = FONT_S)

    draw_text.text((1408, 25), 'За все время', fill = 'white', font = FONT_M)

    draw_text.text((1344, 98), 'Самые популярные', fill = 'white', font = FONT_L)

    rotated_card1 = images[12].convert("RGBA").resize((226, 382)).rotate(25, expand = True)
    rotated_card2 = images[13].convert("RGBA").resize((226, 382)).rotate(-25, expand = True)
    image.paste(rotated_card1, (1156, 200), rotated_card1)
    image.paste(rotated_card2, (1524, 200), rotated_card2)
    image.paste(images[14].resize((226, 382)), (1400, 200))

    draw_text.text((1218, 205), str(card_counts[12]), fill = 'white', font = FONT_M)
    draw_text.text((1490, 160), str(card_counts[13]), fill = 'white', font = FONT_M)
    draw_text.text((1780, 205), str(card_counts[14]), fill = 'white', font = FONT_M)

    draw_text.text((1450, 640), 'Самые', fill = 'white', font = FONT_L)
    draw_text.text((1395, 700), 'непопулярные', fill = 'white', font = FONT_L)

    rotated_card1 = images[15].convert("RGBA").resize((140, 235)).rotate(25, expand = True)
    rotated_card2 = images[16].convert("RGBA").resize((140, 235)).rotate(-25, expand = True)
    image.paste(rotated_card1, (1307, 786), rotated_card1)
    image.paste(rotated_card2, (1535, 786), rotated_card2)
    image.paste(images[17].resize((140, 235)), (1460, 786))

    draw_text.text((1340, 786), str(card_counts[15]), fill = 'white', font = FONT_S)
    draw_text.text((1520, 750), str(card_counts[16]), fill = 'white', font = FONT_S)
    draw_text.text((1700, 786), str(card_counts[17]), fill = 'white', font = FONT_S)

    draw_text.text((675, 25), "Статистика раскладов", fill = 'white', font = FONT_L)
    draw_text.text((735, 150), f"За все время: {stats_count['total_count']}", fill = 'white', font = FONT_L)
    draw_text.text((760, 250), f"За день: {stats_count['daily_count']}", fill = 'white', font = FONT_L)
    draw_text.text((743, 350), f"За неделю: {stats_count['weekly_count']}", fill = 'white', font = FONT_L)
    draw_text.text((750, 450), f"За месяц: {stats_count['monthly_count']}", fill = 'white', font = FONT_L)

    return image
