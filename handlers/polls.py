import json
import time

from aiogram import Router, F
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile, PollAnswer
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import list_members
from bot_instance import bot
from states import WaitForMessage
from storage import poll_storage, poll_meta

router = Router()


@router.message(F.text, StateFilter(WaitForMessage.create_pool))
async def send_poll(message: Message, state: FSMContext):
    pool_data = message.text.split("/")
    question = pool_data[0]
    options = pool_data[-1].split()

    state_data = await state.get_data()
    user_text = state_data['user_msg']
    btn1_text = state_data['btn1_text']
    btn2_text = state_data['btn2_text']

    if len(list_members) < 1:
        cry = FSInputFile("assets/cry.jpeg")
        await message.answer_photo(
            photo=cry,
            caption="Либо ты не добавил ID друзей в list_members либо у тебя их нет..."
        )
        return

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=btn1_text, callback_data="yes"))
    builder.add(InlineKeyboardButton(text=btn2_text, callback_data="no"))

    await message.answer(
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
            'is_pool': True,
            'pool': {
                'question': question,
                'options': options
            }
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

    for friend_id in list_members:
        sent = await bot.send_poll(
            chat_id=friend_id,
            question=question,
            options=options,
            is_anonymous=False,
            allows_multiple_answers=False,
        )
        poll_id = sent.poll.id
        poll_storage[poll_id] = {}
        poll_meta[poll_id] = {
            "question": sent.poll.question,
            "options": options,
            "chat_id": message.chat.id,
        }

    await message.answer(f"Опрос создан. ID: `{poll_id}`")


@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id
    username = poll_answer.user.username or "Unknown"
    option_ids = poll_answer.option_ids

    if not option_ids:
        poll_storage.get(poll_id, {}).pop(user_id, None)
        print(f"@{username} отозвал голос в опросе {poll_id}")
        return

    if poll_id not in poll_storage:
        poll_storage[poll_id] = {}

    poll_storage[poll_id][user_id] = option_ids

    meta = poll_meta.get(poll_id, {})
    options = meta.get("options", [])
    chosen = [options[i] for i in option_ids if i < len(options)]

    await bot.send_message(
        chat_id=user_id,
        text=f"✅ Ваш ответ записан: {', '.join(chosen)}"
    )


@router.callback_query(F.data == 'pool_results')
async def show_results(callback: CallbackQuery):
    if not poll_storage:
        await callback.message.answer("Нет данных об опросах.")
        await callback.answer()
        return

    text = "📊 Результаты опросов:\n\n"

    for poll_id, votes in poll_storage.items():
        meta = poll_meta.get(poll_id, {})
        options = meta.get("options", [])
        question = meta.get("question", poll_id)

        counts = {i: 0 for i in range(len(options))}
        for user_votes in votes.values():
            for opt_id in user_votes:
                counts[opt_id] = counts.get(opt_id, 0) + 1

        text += f"❓ {question}\n"
        for i, option in enumerate(options):
            text += f"  {option}: {counts[i]} голос(ов)\n"
        text += f"  Всего проголосовало: {len(votes)}\n\n"

    await callback.message.answer(text)
    await callback.answer()