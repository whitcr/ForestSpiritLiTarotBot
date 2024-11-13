from PIL import Image, ImageDraw, ImageFont
import os


def create_large_checkmark(draw, x, y, size=60, color="red", width=6):
    start_x = x - size // 2
    start_y = y
    middle_x = x - size // 6
    middle_y = y + size // 2
    end_x = x + size // 2
    end_y = y - size // 2

    for offset in range(-width // 2, width // 2):
        draw.line(
            [(start_x + offset, start_y),
             (middle_x + offset, middle_y),
             (end_x + offset, end_y - offset)],
            fill = color, width = 3
        )


def add_db_numbers(draw, width, height, personal_number, friend_number, font_size=40):
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text_personal = f"({personal_number})"
    draw.text(
        (width * 0.85, height * 0.05),
        text_personal,
        fill = "white",
        font = font
    )

    text_friend = f"({friend_number})"
    draw.text(
        (width * 0.85, height * 0.65),
        text_friend,
        fill = "white",
        font = font
    )


def mark_bonuses(image_path, personal_bonus_number, friend_bonus_number, output_path):
    img = Image.open(image_path)
    width, height = img.size
    draw = ImageDraw.Draw(img)

    personal_bonus_positions = {
        4: (width * 0.2, height * 0.17),  # Расклад на неделю от ли
        12: (width * 0.4, height * 0.17),  # Расклад на месяц от ли
        20: (width * 0.6, height * 0.17),  # Week премиум
        28: (width * 0.8, height * 0.17),  # Month премиум

        # Middle row
        7: (width * 0.25, height * 0.45),  # 20% скидка
        16: (width * 0.5, height * 0.45),  # Free вопрос
        24: (width * 0.75, height * 0.45),  # 2 Free вопроса
    }

    friend_bonus_positions = {
        1: (width * 0.15, height * 0.8),  # 20% скидка
        3: (width * 0.3, height * 0.8),  # Week премиум
        5: (width * 0.45, height * 0.8),  # 2 Free вопроса
        7: (width * 0.6, height * 0.8),  # 3 Free вопроса
        9: (width * 0.75, height * 0.8),  # Month премиум
        12: (width * 0.9, height * 0.8),  # 4 Free вопроса
    }

    for number, position in personal_bonus_positions.items():
        if number <= personal_bonus_number:
            create_large_checkmark(draw, position[0], position[1])

    for number, position in friend_bonus_positions.items():
        if number <= friend_bonus_number:
            create_large_checkmark(draw, position[0], position[1])

    add_db_numbers(draw, width, height, personal_bonus_number, friend_bonus_number)

    img.save(output_path)


if __name__ == "__main__":
    mark_bonuses(
        image_path = "../../images/tech/bonusCards/bonusCard1.png",
        personal_bonus_number = 16,
        friend_bonus_number = 5,
        output_path = "marked_bonus_circles.png"
    )
