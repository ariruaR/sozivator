import asyncio
from bot_instance import bot, dp
from handlers import register_all_routers


async def main():
    register_all_routers(dp)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())