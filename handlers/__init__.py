from aiogram import Router

from handlers.admin import router as admin_router
from handlers.broadcast import router as broadcast_router
from handlers.responses import router as responses_router
from handlers.losers import router as losers_router
from handlers.polls import router as polls_router


def register_all_routers(dp):
    dp.include_router(admin_router)
    dp.include_router(broadcast_router)
    dp.include_router(responses_router)
    dp.include_router(losers_router)
    dp.include_router(polls_router)