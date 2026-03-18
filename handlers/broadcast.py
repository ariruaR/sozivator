import json
import time

from aiogram import Router, F
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import list_members
from bot_instance import bot
from states import WaitForMessage

router = Router()


@router.callback_query(F.data == 'start')
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Напиши сообщение, которое ты хочешь отправить: ")
    await state.set_state(WaitForMessage.wait_msg)
    await callback.answer()


@router.message(F.text, StateFilter(WaitForMessage.wait_msg))
async def wait_msg(message: Message, state: FSMContext):
    await state.update_data(user_msg=message.text)
    await message.answer("Теперь отправьте текст для 1 кнопки (Если друг согласен): ")
    await state.set_state(WaitForMessage.wait_btn1)


@router.message(F.text, StateFilter(WaitForMessage.wait_btn1))
async def wait_btn1(message: Message, state: FSMContext):
    await state.update_data(btn1_text=message.text)
    await message.answer("Теперь отправьте текст для 2 кнопки (Если друг не согласен): ")
    await state.set_state(WaitForMessage.wait_pool)


@router.message(F.text, StateFilter(WaitForMessage.wait_pool))
async def wait_pool(message: Message, state: FSMContext):
    await state.update_data(btn2_text=message.text)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data="create_pool"))
    builder.add(InlineKeyboardButton(text="Нет", callback_data="skip"))
    await message.answer("Создать опрос за место?", reply_markup=builder.as_markup())


@router.callback_query(F.data == 'create_pool')
async def create_pool_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Напиши текст вопроса а потом через '/' все варианты через пробел: "
    )
    await state.set_state(WaitForMessage.create_pool)
    await callback.answer()


@router.callback_query(F.data == 'skip')
async def skip_pool(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()

    user_text = state_data['user_msg']
    btn1_text = state_data['btn1_text']
    btn2_text = state_data['btn2_text']

    if len(list_members) < 1:
        cry = FSInputFile("assets/cry.jpeg")
        await callback.message.answer_photo(
            photo=cry,
            caption="Либо ты не добавил ID друзей в list_members либо у тебя их нет..."
        )
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=btn1_text, callback_data="yes"))
    builder.add(InlineKeyboardButton(text=btn2_text, callback_data="no"))

    await callback.message.answer(
        "Запускаю рассылку...\n"
        "Чтобы посмотреть список тех кто отказался: /losers_list"
    )

    metadata = {
        "Рассылка": {
            'user_text': user_text,
            'btn1_text': btn1_text,
            'btn2_text': btn2_text,
            'time': time.time(),
            'count_users': len(list_members),
            'is_pool': False
        }
    }
    with open("databases/metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

    mem = FSInputFile("assets/skala.webp")
    for member_id in list_members:
        await bot.send_photo(
            chat_id=member_id, photo=mem,
            caption=user_text, reply_markup=builder.as_markup()
        )
    await state.clear()
    await callback.answer()


@router.message(F.text, StateFilter(WaitForMessage.start_last))
async def start_last(message: Message, state: FSMContext):
    if message.text.lower().strip() == 'да':
        with open("databases/metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        user_text = metadata['Рассылка']['user_text']
        btn1_text = metadata['Рассылка']['btn1_text']
        btn2_text = metadata['Рассылка']['btn2_text']

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text=btn1_text, callback_data="yes"))
        builder.add(InlineKeyboardButton(text=btn2_text, callback_data="no"))

        await message.answer(
            "Запускаю последнюю рассылку...\n"
            "Чтобы посмотреть список тех кто отказался: /losers_list"
        )

        metadata['Рассылка']['time'] = time.time()
        with open("databases/metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

        mem = FSInputFile("assets/skala.webp")
        for member_id in list_members:
            await bot.send_photo(
                chat_id=member_id, photo=mem,
                caption=user_text, reply_markup=builder.as_markup()
            )
        await state.clear()
    else:
        await message.answer("Напиши сообщение, которое ты хочешь отправить: ")
        await state.set_state(WaitForMessage.wait_msg)


@router.message(StateFilter(
    WaitForMessage.wait_msg,
    WaitForMessage.wait_btn1,
    WaitForMessage.wait_btn2,
))
async def cancel_msg(message: Message):
    await message.answer("Отправить можно только текст :(")