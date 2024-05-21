# import os
# from PIL import Image
#
#
# # def create():
# #     for i in range(0, 2):
# #         cursor.execute(f"SELECT general FROM meaning_deviantmoon where number ={i}")
# #         text = cursor.fetchall()
# #         text = text.replace("\n", "")
# #         cursor.execute(f"UPDATE meaning_deviantmoon SET general = %s WHERE number = %s", (text, i))
# #         db.commit()
# # create()
# #
# # import re
# #
# # async def create():
# #         for i in range(0, 78):
# #             cursor.execute(f"SELECT history FROM meaning_deviantmoon where number ={i}")
# #             text = cursor.fetchone()[0]
# #             text = re.sub(r'[\r\n]+', '', text)
# #             text = text.replace("\n", "")
# #             text = text.replace(",", ", ")
# #             text = text.replace("\\n", "")
# #             text = text.replace(".", ". ")
# #             text = text.replace("  ", " ")
# #             cursor.execute(f"UPDATE meaning_deviantmoon SET history = %s WHERE number = %s", (text, i))
# #
# #         db.commit()
#
#
# from PIL import Image
# import os
#
# def rotate_image(image_path):
#     image = Image.open(image_path)
#     rotated_image = image.rotate(90, expand=True)
#     rotated_image.save(image_path)
#
# # Указать путь к папке с изображениями
# folder_path = "./tech/background"
#
# # Получить список файлов в папке
# file_list = os.listdir(folder_path)
#
# # Обработать каждый файл
# for file_name in file_list:
#     # Полный путь к файлу
#     file_path = os.path.join(folder_path, file_name)
#
#     # Проверить, является ли файл изображением
#     if os.path.isfile(file_path) and file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
#         rotate_image(file_path)
#         print(f"Изображение {file_name} успешно повернуто и сохранено.")
#     else:
#         print(f"Файл {file_name} не является изображением или не поддерживается.")


from PIL import Image
import os

def resize_images_in_folder(input_folder, output_folder, target_size=(500, 830)):
    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Пропускаем, если это не изображение
        if not os.path.isfile(input_path) or not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            continue

        # Открываем изображение
        with Image.open(input_path) as img:
            # Изменяем размер
            resized_img = img.resize(target_size, Image.ANTIALIAS)

            # Сохраняем измененное изображение в выходную папку
            resized_img.save(output_path)
            print(f"Изображение '{filename}' успешно изменено")

input_folder = "cards/joytarot"  # Замените на свой путь
output_folder = "cards/joytarot1"  # Замените на свой путь

resize_images_in_folder(input_folder, output_folder)
