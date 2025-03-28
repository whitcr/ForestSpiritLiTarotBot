from aiogram import types, Router, F

from database import execute_select, execute_query
from filters.baseFilters import IsReply
from filters.subscriptions import SubscriptionLevel
from functions.cards.create import get_choice_spread
from functions.messages.messages import get_reply_message, typing_animation_decorator, delete_message

from functions.gpt.requests import get_cards_meanings, get_cards_meanings_details

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.filters.callback_data import CallbackData
from typing import Optional
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.tarot.spreads.spreadsConfig import SPREADS, get_name_by_cb_key, get_questions_by_name


class ChangeQuestionState(StatesGroup):
    waiting_for_question = State()


class ChangeSituationState(StatesGroup):
    waiting_for_situation = State()


class ChangeDetailsState(StatesGroup):
    waiting_for_details = State()


router = Router()


class GptCallbackMeaning(CallbackData, prefix = "get_def_gpt_"):
    card_1: int
    d1card_1: Optional[int]
    d2card_1: Optional[int]
    d3card_1: Optional[int]

    card_2: int
    d1card_2: Optional[int]
    d2card_2: Optional[int]
    d3card_2: Optional[int]

    card_3: int
    d1card_3: Optional[int]
    d2card_3: Optional[int]
    d3card_3: Optional[int]

    spread_name: Optional[str]

    premium: Optional[bool]

    question: Optional[str]
    situation: Optional[str]


async def create_gpt_keyboard(user_id, buttons, nums, prev_callback_data=None, card_position=None, dop_num=None,
                              spread_name=None):
    def create_callback_data(nums, d1cards, d2cards, d3cards, premium=False, question=None, situation=None,
                             spread_name=None):
        return GptCallbackMeaning(
            card_1 = nums[0], d1card_1 = d1cards[0],
            d2card_1 = d2cards[0],
            d3card_1 = d3cards[0],
            card_2 = nums[1], d1card_2 = d1cards[1],
            d2card_2 = d2cards[1],
            d3card_2 = d3cards[1],
            card_3 = nums[2], d1card_3 = d1cards[2],
            d2card_3 = d2cards[2],
            d3card_3 = d3cards[2],
            spread_name = SPREADS[spread_name]['cb_key'] if spread_name else None,
            premium = premium,
            question = question,
            situation = situation
        ).pack()

    d1cards = [None, None, None]
    d2cards = [None, None, None]
    d3cards = [None, None, None]

    if prev_callback_data is not None and dop_num is not None:
        callback = GptCallbackMeaning.unpack(prev_callback_data)
        d1cards = [callback.d1card_1, callback.d1card_2, callback.d1card_3]
        d2cards = [callback.d2card_1, callback.d2card_2, callback.d2card_3]
        d3cards = [callback.d3card_1, callback.d3card_2, callback.d3card_3]

        if card_position == 1:
            if d1cards[0] is None:
                d1cards[0] = dop_num
            elif d2cards[0] is None:
                d2cards[0] = dop_num
            elif d3cards[0] is None:
                d3cards[0] = dop_num
        elif card_position == 2:
            if d1cards[1] is None:
                d1cards[1] = dop_num
            elif d2cards[1] is None:
                d2cards[1] = dop_num
            elif d3cards[1] is None:
                d3cards[1] = dop_num
        elif card_position == 3:
            if d1cards[2] is None:
                d1cards[2] = dop_num
            elif d2cards[2] is None:
                d2cards[2] = dop_num
            elif d3cards[2] is None:
                d3cards[2] = dop_num

    callback_data_default = create_callback_data(nums, d1cards, d2cards, d3cards, spread_name = spread_name)
    callback_data_premium = create_callback_data(nums, d1cards, d2cards, d3cards, premium = True,
                                                 spread_name = spread_name)

    buttons.extend([[InlineKeyboardButton(text = 'Трактовка', callback_data = callback_data_default),
                     InlineKeyboardButton(text = 'Трактовка+', callback_data = callback_data_premium)]])

    return buttons


async def format_callback_data(call, data):
    get_question, get_theme = None, None
    get_cards = []

    question = call.message.reply_to_message.text.replace("триплет", "")
    if question.strip():
        get_question = question

    spread_key = data.get('spread_name')
    if spread_key:
        get_theme = await get_name_by_cb_key(spread_key)

    for i in range(0, 4):
        card = data.get(f'card_{i}')
        if card is not None:
            card_name = await execute_select("SELECT name FROM cards WHERE number = $1", (card,))
            line = f"Карта {i}: {card_name}."
            additional_cards = []
            for j in range(1, 4):
                d = data.get(f'd{str(j)}card_{i}')
                if d is not None:
                    card_name_d = await execute_select("SELECT name FROM cards WHERE number = $1", (d,))
                    additional_cards.append(card_name_d)
            if additional_cards:
                line += f" Дополнительные карты: {', '.join(additional_cards)}"
            get_cards.append(line)
    return "\n".join(get_cards), get_question, get_theme


@router.callback_query(IsReply(), GptCallbackMeaning.filter(F.premium == True), SubscriptionLevel(2))
async def get_gpt_response_cards_meaning(call: types.CallbackQuery, callback_data: GptCallbackMeaning,
                                         state: FSMContext):
    await call.answer()

    choice = await get_choice_spread(call.from_user.id)
    if choice != 'raider':
        await call.message.answer("Трактовки могут быть сделаны только для колоды Райдер-Уэйт.")
        return

    count = await  execute_select("select paid_meanings from users where user_id = $1", (call.from_user.id,))
    if count > 0:
        await execute_query("update users set paid_meanings = paid_meanings - 1 where user_id = $1",
                            (call.from_user.id,))
    else:
        await call.message.answer("У вас закончились платные трактовки.")
        return

    data_dict = callback_data.model_dump()

    get_cards, get_question, get_theme = await format_callback_data(call, data_dict)

    text = ""
    if get_theme:
        text += f"Тема: {get_theme}. \n\n"
    if get_question:
        text += f"Вопрос: {get_question}. \n\n"
    if get_cards:
        text += f"{get_cards}"

    await state.update_data(get_cards = get_cards, get_question = get_question, get_theme = get_theme)
    await get_cards_meanings_premium(call, state)


@router.callback_query(IsReply(), GptCallbackMeaning.filter(F.premium == False), SubscriptionLevel(1, True))
@typing_animation_decorator(initial_message = "Трактую")
async def get_gpt_response_cards_meaning(call: types.CallbackQuery, callback_data: GptCallbackMeaning):
    await call.answer()

    choice = await get_choice_spread(call.from_user.id)
    if choice != 'raider':
        await call.message.answer("Трактовки могут быть сделаны только для колоды Райдер-Уэйт.")
        return

    count = await execute_select("select paid_meanings from users where user_id = $1", (call.from_user.id,))
    if count > 0:
        await execute_query("update users set paid_meanings = paid_meanings - 1 where user_id = $1",
                            (call.from_user.id,))
    else:
        await call.message.answer("У вас закончились платные трактовки.")
        return

    data_dict = callback_data.model_dump()

    get_cards, get_question, get_theme = await format_callback_data(call, data_dict)

    text = ""
    if get_question:
        if get_theme:
            text += f"Тема: {get_theme}. \n\n"

            questions = await get_questions_by_name(get_theme)

            text += f"Вопрос для 1 карты: {questions[0]}. \n\n"
            text += f"Вопрос для 2 карты: {questions[1]}. \n\n"
            text += f"Вопрос для 3 карты: {questions[2]}. \n\n"
        else:
            text += f"Вопрос: {get_question}. \n\n"
    if get_cards:
        text += f"{get_cards}"

    message = await get_cards_meanings(text)
    await call.message.answer(message, reply_to_message_id = call.message.message_id)
    # await call.message.answer(text)


async def get_text_for_meaning(data):
    get_cards = data.get('get_cards')
    get_question = data.get('get_question')
    get_theme = data.get('get_theme')
    get_situation = data.get('get_situation')
    get_details = data.get('get_details')
    get_details_questions = data.get('get_details_questions')

    text = ""
    if get_theme:
        text += f"Тема: {get_theme}. \n\n"
    if get_question:
        text += f"Вопрос: {get_question} \n\n"
    if get_situation:
        text += f"Ситуация: {get_situation} \n\n"
    if get_cards:
        text += f"{get_cards}\n\n"
    if get_details:
        text += f"Уточняющие вопросы клиенту: \n{get_details_questions}\n\nОтветы клиента:\n{get_details}\n\n"

    return text


async def get_cards_meanings_premium(call, state: FSMContext):
    data = await state.get_data()
    text = await get_text_for_meaning(data)

    keyboard_buttons = [
        [InlineKeyboardButton(text = 'Изменить вопрос', callback_data = "change_question")],
        [InlineKeyboardButton(text = 'Описать ситуацию', callback_data = "change_situation")],
        [InlineKeyboardButton(text = 'Трактовка', callback_data = "get_meaning_premium")],
    ]

    if data.get('get_details') is None:
        keyboard_buttons.append([InlineKeyboardButton(text = 'Уточнить', callback_data = "get_details")])

    premium_inline_kb = InlineKeyboardMarkup(inline_keyboard = keyboard_buttons)

    message_text = (
        f"Информация про расклад: \n\n{text}"
        f"Если вы хотите изменить вопрос или ситуацию, нажмите на одну из кнопок ниже."
        f"Нажмите на кнопку 'Уточнить', чтобы трактовка была более четкой. (Опционально) \n\n "
    )

    if data.get('get_message'):
        reply_message = data.get('get_message')
    else:
        reply_message = call.message.message_id

    try:
        await call.message.answer(text = message_text, reply_markup = premium_inline_kb,
                                  reply_to_message_id = reply_message)
    except:
        await call.answer(text = message_text, reply_markup = premium_inline_kb,
                          reply_to_message_id = reply_message)


@router.callback_query(IsReply(), F.data == "change_question")
async def change_question(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    await delete_message(call.message)
    bot_message = await call.message.answer("Введите новый вопрос:",
                                            reply_to_message_id = await get_reply_message(call))
    await state.update_data(get_message = await get_reply_message(call), bot_message = bot_message)
    await state.set_state(ChangeQuestionState.waiting_for_question)


@router.message(ChangeQuestionState.waiting_for_question)
async def process_new_question(message: types.Message, state: FSMContext):
    new_question = message.text
    await delete_message(message)
    state_data = await state.get_data()
    await delete_message(state_data.get("bot_message"))

    await state.update_data(get_question = new_question)
    await get_cards_meanings_premium(call = message, state = state)


@router.callback_query(IsReply(), F.data == "change_situation")
async def change_situation(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

    await delete_message(call.message)
    bot_message = await call.message.answer("Введите описание ситуации:",
                                            reply_to_message_id = await get_reply_message(call))
    await state.update_data(get_message = await get_reply_message(call), bot_message = bot_message)
    await state.set_state(ChangeSituationState.waiting_for_situation)


@router.message(ChangeSituationState.waiting_for_situation)
async def process_new_situation(message: types.Message, state: FSMContext):
    new_situation = message.text
    await delete_message(message)
    state_data = await state.get_data()
    await delete_message(state_data.get("bot_message"))
    await state.update_data(get_situation = new_situation)
    await get_cards_meanings_premium(call = message, state = state)


@router.callback_query(IsReply(), F.data == "get_details", SubscriptionLevel(3))
async def change_details(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await delete_message(call.message)
    data = await state.get_data()
    text = await get_text_for_meaning(data)

    message = await get_cards_meanings_details(text)
    await state.update_data(get_details_questions = message)
    bot_message = await call.message.answer(message,
                                            reply_to_message_id = await get_reply_message(call))
    await state.update_data(get_message = await get_reply_message(call), bot_message = bot_message)
    await state.set_state(ChangeDetailsState.waiting_for_details)


@router.message(ChangeDetailsState.waiting_for_details)
async def process_new_details(message: types.Message, state: FSMContext):
    new_details = message.text
    await delete_message(message)
    state_data = await state.get_data()
    await delete_message(state_data.get("bot_message"))
    await state.update_data(get_details = new_details)
    await get_cards_meanings_premium(call = message, state = state)


@router.callback_query(IsReply(), F.data == "get_meaning_premium")
@typing_animation_decorator(initial_message = "Трактую")
async def get_meaning_premium(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await delete_message(call.message)
    await state.clear()

    message = await get_cards_meanings(call.message.text)
    await call.message.answer(message,
                              reply_to_message_id = await get_reply_message(call))
