from aiogram.fsm.state import State, StatesGroup


class WaitForMessage(StatesGroup):
    start_last = State()
    wait_msg = State()
    wait_btn1 = State()
    wait_btn2 = State()
    wait_pool = State()
    create_pool = State()