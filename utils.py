import asyncio
import random

from bot_instance import bot
from storage import ACTIVE_SESSION


async def punish_slackers(target_ids):
    """Раз в 10 минут шлёт 'люлей' тем, кто не ответил."""
    while True:
        await asyncio.sleep(600)

        for user_id, ignore in ACTIVE_SESSION.items():
            try:
                with open('assets/phrases.txt', 'r', encoding='UTF-8') as file:
                    phrases_list = file.readlines()
                if phrases_list and ignore is None:
                    await bot.send_message(user_id, random.choice(phrases_list))
            except Exception as e:
                print(f"Не удалось достать до {user_id}: {e}")