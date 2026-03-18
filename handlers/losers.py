import json
import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot_instance import bot

router = Router()


async def _build_losers_text():
    """Формирует текст рейтинга позора и флаг наличия данных."""
    if not os.path.exists("databases/losers.json"):
        return None, False

    with open("databases/losers.json", "r", encoding="utf-8") as f:
        losers_data = json.load(f)

    if not losers_data:
        return None, False

    sorted_losers = sorted(losers_data.items(), reverse=True)
    medals = ["🥇", "🥈", "🥉"]

    text = "📊 **ОФИЦИАЛЬНЫЙ РЕЙТИНГ ПОЗОРА:**\n\n"
    for i, (user_id, info) in enumerate(sorted_losers):
        rank = medals[i] if i < 3 else "🔹"
        name = info['name']
        count = info['count']
        text += f"{rank} `{name}` — {count} раз(а)\n"

    return text, True


@router.message(Command("losers_list"))
async def losers_list_command(message: Message):
    text, has_data = await _build_losers_text()

    if has_data:
        loser_gif = FSInputFile("assets/deathNote.gif")
        await bot.send_animation(
            message.chat.id, animation=loser_gif,
            caption=text, parse_mode="Markdown"
        )
    else:
        peacedog = FSInputFile("assets/peacedog.webp")
        await message.answer_photo(
            photo=peacedog,
            caption="Список предателей пока пуст. "
                    "Либо все идут гулять, либо ты еще никому не писал! 😇"
        )


@router.callback_query(F.data == 'losers_list')
async def losers_list_callback(callback: CallbackQuery):
    text, has_data = await _build_losers_text()

    if has_data:
        loser_gif = FSInputFile("assets/deathNote.gif")
        await bot.send_animation(
            callback.message.chat.id, animation=loser_gif,
            caption=text, parse_mode="Markdown"
        )
    else:
        peacedog = FSInputFile("assets/peacedog.webp")
        await callback.message.answer_photo(
            photo=peacedog,
            caption="Список предателей пока пуст. "
                    "Либо все идут гулять, либо ты еще никому не писал! 😇"
        )
    await callback.answer()