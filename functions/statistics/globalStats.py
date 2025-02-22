from PIL import Image, ImageDraw, ImageFont


async def generate_stats_image(stats):
    """Генерирует профессиональное изображение статистики команд."""
    width, height = 800, 150 + len(stats) * 80
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        text_font = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Заголовок
    draw.rectangle([(20, 20), (width - 20, 80)], fill = "#4CAF50", outline = "black", width = 3)
    draw.text((width // 2 - 150, 30), "📊 Статистика команд", fill = "white", font = title_font)

    # Полупрозрачный фон для данных
    draw.rectangle([(20, 100), (width - 20, height - 20)], fill = "#f0f0f0", outline = "black", width = 3)

    y = 120
    for stat in stats:
        text = f"{stat[0]} - Д: {stat[1]} | Н: {stat[2]} | М: {stat[3]} | Всего: {stat[4]}"
        draw.text((40, y), text, fill = "black", font = text_font)
        y += 70

    return img
