import json
import os
import time

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from bot_instance import bot
from storage import ACTIVE_SESSION

router = Router()


@router.callback_query(F.data == 'yes')
async def yes_callback(callback: CallbackQuery):
    current_time = time.time()
    ACTIVE_SESSION[callback.from_user.id] = True

    with open("databases/metadata.json", 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    if round(current_time - metadata['Рассылка']['time'], 1) > 10 * 60:
        await callback.message.answer(
            "Ты конечно красава, но мог бы и побыстрее отвечать😒"
        )
        await callback.answer()
        return

    await callback.message.answer("Чувак да ты крут!")
    await callback.answer()


@router.callback_query(F.data == 'no')
async def no_callback(callback: CallbackQuery):
    current_time = time.time()

    with open("databases/metadata.json", 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    text = 'Позорище'
    if round(current_time - metadata['Рассылка']['time'], 1) > 10 * 60:
        text = 'ТЫ не просто позорище, ты еще и ленивое позорище! Отвечай быстрее'

    await callback.answer(text=text, show_alert=True)

    fullname = callback.from_user.full_name
    user_id = str(callback.from_user.id)
    ACTIVE_SESSION[callback.from_user.id] = False

    # Обновляем файл лузеров
    if os.path.exists("databases/losers.json"):
        with open("databases/losers.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if user_id in data:
        data[user_id]['count'] += 1
    else:
        data[user_id] = {'name': fullname, 'count': 1}

    with open("databases/losers.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    gif = FSInputFile("assets/cat.gif")
    await callback.message.answer_animation(animation=gif)
    await callback.answer()