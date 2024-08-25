from aiogram import types, Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
import keyboard as kb
import re
from constants import CARDS_NAME_SYNONYMS
from database import execute_select
from functions.cards.create import get_choice_spread, get_path_cards
from functions.store.temporaryStore import store_data
from handlers.tarot.meaningCards.meaningCb import generate_meaning_keyboard, MEANINGS_BUTTONS

router = Router()


async def replace_synonyms(text):
    words = text.lower().split()
    for i, word in enumerate(words):
        for key, synonyms_list in CARDS_NAME_SYNONYMS.items():
            if word in synonyms_list:
                words[i] = key
    name = " ".join(words)
    text = text.lower()
    for i in enumerate(text):
        for key, synonyms_list in CARDS_NAME_SYNONYMS.items():
            if text in synonyms_list:
                name = key
    return name


@router.message(F.text.lower().startswith("значение"))
async def get_meaning(message: types.Message, bot: Bot):
    if re.search(r'значение\Z', message.text.lower()):
        await message.answer(
            f"<code>— Пример ввода команды: значение шут, значение десятка чаш, значение иерофант </code>")
    else:
        try:
            name = await replace_synonyms(" ".join(message.text.split()[1:]))

            num = await execute_select("SELECT number FROM meaning_raider WHERE name = $1;", (name,))

            choice = await get_choice_spread(message.from_user.id)
            card_paths = await get_path_cards(choice, num)
            table = f"meaning_{choice}"
            if choice in MEANINGS_BUTTONS.keys():
                meaning_text = await execute_select(f"select general from {table} where number = $1;", (num,))

                if len(meaning_text) > 4000:
                    meaning_text = meaning_text[:4000]

                text = meaning_text + f"\n\n<a href = '{MEANINGS_BUTTONS[choice]['source']}'>Источник</a>"

                keyboard = await generate_meaning_keyboard(choice, f'meaning_{choice}_general')

                await bot.send_photo(message.chat.id, photo = FSInputFile(card_paths, 'rb'),
                                     reply_to_message_id = message.message_id)
                msg = await bot.send_message(message.chat.id, text, reply_markup = keyboard,
                                             reply_to_message_id = message.message_id)
                if message.chat.type == "private":
                    await message.answer("— Вернуть удобное меню с командами?", reply_markup = kb.menu_return_keyboard)

                await store_data(msg, num)
            else:
                await message.reply(
                    f"— К сожалению, пока что у меня нет значений на выбранную колоду. "
                    f"Значение есть только для Уэйта, Безумной Луны, Чеколли и Манары.")
                return
        except Exception as e:
            await message.reply(f"— Такой карты нет, попробуйте снова. ", reply_markup = kb.menu_private_keyboard)


class MeaningClass(StatesGroup):
    card = State()


@router.message(StateFilter(None), F.text.lower() == "узнать значение")
async def get_meaning_command(message: types.Message, state: FSMContext):
    await message.reply(
        f"— О какой карте вы бы хотели узнать больше?\n<code>Пример: Десятка чаш, Жрица, Иерофант, "
        f"Королева мечей.</code>",
        reply_markup = types.ReplyKeyboardRemove())
    await state.set_state(MeaningClass.card)


@router.message(MeaningClass.card)
async def get_meaning_text(message: types.Message, state: FSMContext, bot: Bot):
    try:
        name = await replace_synonyms(" ".join(message.text.split()))
        num = await execute_select("select number from meaning_raider where name = $1;", (name.lower(),))

        choice = await get_choice_spread(message.from_user.id)
        card_paths = await get_path_cards(choice, num)
        table = f"meaning_{choice}"
        print(table, num)
        if choice in ['raider', "manara", 'deviantmoon', 'ceccoli']:
            meaning_text = await execute_select(f"select general from {table} where number = $1;", (num,))

            text = meaning_text + f"\n\n<a href = '{MEANINGS_BUTTONS[choice]['source']}'>Источник</a>"

            keyboard = await generate_meaning_keyboard(choice, f'meaning_{choice}_general')
            await bot.send_photo(message.chat.id, photo = FSInputFile(card_paths, 'rb'),
                                 reply_to_message_id = message.message_id)
            msg = await bot.send_message(message.chat.id, text, reply_markup = keyboard,
                                         reply_to_message_id = message.message_id)
            if message.chat.type == "private":
                await message.answer("— Вернуть удобное меню с командами?", reply_markup = kb.menu_return_keyboard)

            await store_data(msg, num)
            await state.clear()
        else:
            await message.reply(
                f"— К сожалению, пока что у меня нет значений на выбранную колоду."
                f"Значение есть только для Уэйта, Безумной Луны, Чеколли и Манары.")
            await state.clear()
    except Exception as e:
        await message.reply(f"— Такой карты нет, попробуйте снова", reply_markup = kb.menu_private_keyboard)
        await state.clear()
