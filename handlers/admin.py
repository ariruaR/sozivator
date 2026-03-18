import json
import time
import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID, list_members
from bot_instance import bot
from states import WaitForMessage
from storage import ACTIVE_SESSION, poll_storage, poll_meta
from utils import punish_slackers

router = Router()


@router.message(Command('admin'))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ отклонен, вы не админ!")
        return

    jarvis = FSInputFile("assets/jarvis.jpg")

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Запустить прошлую рассылку",
        callback_data="start_last"))
    builder.add(InlineKeyboardButton(
        text="Лист лузеров",
        callback_data="losers_list"))
    builder.add(InlineKeyboardButton(
        text="Начать новую рассылку",
        callback_data="start"))
    builder.add(InlineKeyboardButton(
        text="Результаты опроса(ов)",
        callback_data="pool_results"))

    await message.answer_photo(
        photo=jarvis,
        caption=f"Приветствую вас, {message.from_user.username}\n Вот ваша админ-панель:",
        reply_markup=builder.as_markup()
    )


@router.message(CommandStart())
async def start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Добро пожаловать в админку: /admin")
    else:
        await message.answer("В ДОСТУПЕ ОТКАЗАНО")


@router.callback_query(F.data == "start_last")
async def start_last_callback(callback: CallbackQuery, state: FSMContext):
    with open("databases/metadata.json", 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    user_text = metadata['Рассылка']['user_text']
    btn1_text = metadata['Рассылка']['btn1_text']
    btn2_text = metadata['Рассылка']['btn2_text']
    is_pool = metadata['Рассылка']['is_pool']

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=btn1_text, callback_data="yes"))
    builder.add(InlineKeyboardButton(text=btn2_text, callback_data="no"))

    await callback.message.answer(
        "Запускаю последнюю рассылку...\n"
        "Чтобы посмотреть список тех кто отказался: /losers_list"
    )

    metadata['Рассылка']['time'] = time.time()
    with open("databases/metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

    mem = FSInputFile("assets/skala.webp")
    for member_id in list_members:
        ACTIVE_SESSION[member_id] = None
        await bot.send_photo(
            chat_id=member_id, photo=mem,
            caption=user_text, reply_markup=builder.as_markup()
        )
    await state.clear()

    if is_pool:
        pool_question = metadata['Рассылка']['pool']['question']
        pool_options = metadata['Рассылка']['pool']['options']
        for friend_id in list_members:
            sent = await bot.send_poll(
                chat_id=friend_id,
                question=pool_question,
                options=pool_options,
                is_anonymous=False,
                allows_multiple_answers=False,
            )
            poll_id = sent.poll.id
            poll_storage[poll_id] = {}
            poll_meta[poll_id] = {
                "question": sent.poll.question,
                "options": pool_options,
                "chat_id": friend_id,
            }
        await callback.message.answer(f"Опрос создан. ID: `{poll_id}`")

    asyncio.create_task(punish_slackers(list_members))
    await callback.answer("Рассылка ушла. Осада запущена! 🔥")