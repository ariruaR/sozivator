# Подпишись на @pythonforkids_easy_clear если не хочешь остаться нпс 

import time
import json
import os
import asyncio
import random
from re import U 
from aiogram import Dispatcher, Bot, F 
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile, PollAnswer
from aiogram.utils.keyboard import InlineKeyboardBuilder 
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup


os.chdir('sozivator')

API_TOKEN = "" #Сюда свой токен 
 
bot = Bot(token=API_TOKEN) 
 
dp = Dispatcher() 



class WaitForMessage(StatesGroup):
    start_last = State()
    wait_msg = State()
    wait_btn1 = State()
    wait_btn2 = State()
    wait_pool = State()
    create_pool = State()
 
ADMIN_ID =  #Сюда свой айдишник
 
list_members = [] #Это список твоих друзей 

ACTIVE_SESSION = {}


async def punish_slackers(target_ids):
    while True:
        await asyncio.sleep(600) # Ждем 10 минут (600 секунд)
        
        # 4. Рассылаем "люлей" оставшимся
        for user_id, ignore in ACTIVE_SESSION.items():
            try:
                with open('assets/phrases.txt', 'r',encoding='UTF-8') as file:
                    phrases_list = file.readlines()
                if phrases_list and ignore == None:
                    await bot.send_message(user_id, random.choice(phrases_list))
            except Exception as e:
                print(f"Не удалось достать до {user_id}: {e}")



@dp.message(Command('admin'))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Доступ отклонен, вы не админ!")
        return
    jarvis = FSInputFile("assets/jarvis.jpg")
   
    builder = InlineKeyboardBuilder() 
    builder.add(InlineKeyboardButton( 
            text="Запустить прошлую рассылку", 
            callback_data="start_last",
            style="success") 
        ) 
    builder.add(InlineKeyboardButton( 
            text="Лист лузеров", 
            callback_data="losers_list",
            style="danger") 
        ) 
    builder.add(InlineKeyboardButton( 
            text="Начать новую рассылку", 
            callback_data="start")
        )  
    builder.add(InlineKeyboardButton( 
            text="Результаты опроса(ов)", 
            callback_data="pool_results")
        )
    await message.answer_photo(photo=jarvis, caption=f"Приветствую вас, {message.from_user.username}\n Вот ваша админ-панель:", reply_markup=builder.as_markup())





@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Добро пожаловать в админку: /admin")
    else:
        await message.answer("В ДОСТУПЕ ОТКАЗАНО")

@dp.callback_query(F.data == 'start')
async def start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Напиши сообщение, которое ты хочешь отправить: ")
    await state.set_state(WaitForMessage.wait_msg)
    await callback.answer()

@dp.callback_query(F.data == "start_last")
async def start_last_callback(callback: CallbackQuery, state: FSMContext):
    with open("databases/metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
    user_text = metadata['Рассылка']['user_text']
    btn1_text = metadata['Рассылка']['btn1_text']
    btn2_text = metadata['Рассылка']['btn2_text']
    is_pool = metadata['Рассылка']['is_pool']
    builder = InlineKeyboardBuilder() 
    builder.add(InlineKeyboardButton( 
        text=btn1_text, 
        callback_data="yes",
        style="success") 
    ) 
    builder.add(InlineKeyboardButton( 
        text=btn2_text, 
        callback_data="no",
        style="danger") 
    )  
    
    await callback.message.answer("Запускаю последнюю рассылку...\n Чтобы посмотреть список тех кто отказался: /losers_list") 
    
    metadata['Рассылка']['time'] = time.time()
    with open("databases/metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    

    mem = FSInputFile("assets/skala.webp")
    for member_id in list_members: 
        ACTIVE_SESSION[member_id] = None
        await bot.send_photo(chat_id=member_id, photo=mem, caption=user_text, reply_markup=builder.as_markup())
        await state.clear()
    await callback.answer()
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

            # Сохраняем метаданные опроса
            poll_storage[poll_id] = {}
            poll_meta[poll_id] = {
                "question": sent.poll.question,
                "options": pool_options,
                "chat_id": friend_id,
            }

        await callback.message.answer(f"Опрос создан. ID: `{poll_id}`")
    asyncio.create_task(punish_slackers(list_members))
    await callback.answer("Рассылка ушла. Осада запущена! 🔥")
    
    
@dp.callback_query(F.data == 'losers_list')
async def losers_list_callback(callback: CallbackQuery, state: FSMContext):
    losers_data = {}
    if os.path.exists("databases/losers.json"):
        with open("databases/losers.json", "r", encoding="utf-8") as f:
            losers_data = json.load(f)
        if not losers_data:
            await callback.message.answer("✨ Список пока пуст.")
            return

    # 1. Сортируем по количеству отказов (от большего к меньшему)
    sorted_losers = sorted(losers_data.items(),reverse=True)

    # 2. Формируем красивый текст
    text = "📊 **ОФИЦИАЛЬНЫЙ РЕЙТИНГ ПОЗОРА:**\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, info) in enumerate(sorted_losers):
        rank = medals[i] if i < 3 else "🔹"
        name = info['name']
        count = info['count']
        
        # Добавляем строку в список
        text += f"{rank} `{name}` — {count} раз(а)\n"

        loser_gif = FSInputFile("assets/deathNote.gif")

        await bot.send_animation(callback.message.chat.id, animation=loser_gif, caption=text, parse_mode="Markdown")
        return
    else:
        peacedog = FSInputFile("assets/peacedog.webp")
        await callback.message.answer_photo(photo=peacedog,caption="Список предателей пока пуст. Либо все идут гулять, либо ты еще никому не писал! 😇")
    await callback.answer()


@dp.message(F.text, StateFilter(WaitForMessage.start_last))
async def start_last(message: Message, state: FSMContext):
    if message.text.lower().strip() == 'да':

        with open("databases/metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        user_text = metadata['Рассылка']['user_text']
        btn1_text = metadata['Рассылка']['btn1_text']
        btn2_text = metadata['Рассылка']['btn2_text']


        builder = InlineKeyboardBuilder() 
        builder.add(InlineKeyboardButton( 
            text=btn1_text, 
            callback_data="yes",
            style="success") 
        ) 
        builder.add(InlineKeyboardButton( 
            text=btn2_text, 
            callback_data="no",
            style="danger") 
        )  
        
        await message.answer("Запускаю последнюю рассылку...\n Чтобы посмотреть список тех кто отказался: /losers_list") 
        
        metadata['Рассылка']['time'] = time.time()
        with open("databases/metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        

        mem = FSInputFile("assets/skala.webp")
        for member_id in list_members: 
            await bot.send_photo(chat_id=member_id, photo=mem, caption=user_text, reply_markup=builder.as_markup())
            await state.clear()
    else:
        await message.answer("Напиши сообщение, которое ты хочешь отправить: ")
        await state.set_state(WaitForMessage.wait_msg)

@dp.message(F.text, StateFilter(WaitForMessage.wait_msg)) 
async def wait_msg(message: Message, state: FSMContext): 
    user_msg = message.text
    await state.update_data(user_msg=user_msg)
    await message.answer("Теперь отправьте текст для 1 кнопки(Если друг согласен): ")
    await state.set_state(WaitForMessage.wait_btn1)

@dp.message(F.text, StateFilter(WaitForMessage.wait_btn1)) 
async def start_msg(message: Message, state: FSMContext): 

    state_data = await state.get_data()
    user_text = state_data['user_msg']

    btn1_text = message.text
    
    await state.update_data(btn1_text=btn1_text)
    await message.answer("Теперь отправьте текст для 2 кнопки(Если друг не согласен): ")
    await state.set_state(WaitForMessage.wait_pool)

@dp.message(F.text, StateFilter(WaitForMessage.wait_pool))
async def wait_pool(message: Message, state: FSMContext):
    await state.update_data(btn2_text=message.text)
    
    builder = InlineKeyboardBuilder() 
    builder.add(InlineKeyboardButton( 
        text="Да", 
        callback_data="create_pool",
        style="success") 
    ) 
    builder.add(InlineKeyboardButton( 
        text="Нет", 
        callback_data="skip",
        style="danger") 
    ) 
    await message.answer("Создать опрос за место?", reply_markup=builder.as_markup())
@dp.callback_query(F.data == 'create_pool')
async def create_pool_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Напиши текст вопроса а потом через '/' все варианты через пробел: ")
    await state.set_state(WaitForMessage.create_pool)

@dp.callback_query(F.data == 'skip')
async def start_msg(message: Message, state: FSMContext): 
    
    state_data = await state.get_data()

    user_text = state_data['user_msg']
    btn1_text = state_data['btn1_text']
    btn2_text = state_data['btn2_text']

    if len(list_members) < 1:
        cry = FSInputFile("assets/cry.jpeg")
        await message.answer_photo(photo=cry, caption="Либо ты не добавил ID друзей в list_members либо у тебя их нет...")
        return 

    builder = InlineKeyboardBuilder() 
    builder.add(InlineKeyboardButton( 
        text=btn1_text, 
        callback_data="yes",
        style="success") 
    ) 
    builder.add(InlineKeyboardButton( 
        text=btn2_text, 
        callback_data="no",
        style="danger") 
    )  
      
    await message.answer("Запускаю рассылку...\n Чтобы посмотреть список тех кто отказался: /losers_list") 
    metadata = {f"Рассылка": 
        {
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
        await bot.send_photo(chat_id=member_id, photo=mem, caption=user_text, reply_markup=builder.as_markup())
        await state.clear()




 
@dp.callback_query(F.data == 'yes') 
async def yes(callback: CallbackQuery): 
    current_time = time.time()

    ACTIVE_SESSION[callback.from_user.id] = True

    with open("databases/metadata.json", 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    if round(current_time - metadata['Рассылка']['time'], 1) > 10*60:
        await callback.message.answer("Ты конечно красава, но мог бы и побыстрее отвечать😒") 
        await callback.answer() 
        return 
    

    await callback.message.answer("Чувак да ты крут!") 
    await callback.answer() 

@dp.callback_query(F.data == 'no') 
async def no(callback: CallbackQuery): 

    current_time = time.time()
    with open("databases/metadata.json", 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    text = 'Позорище'
    if round(current_time - metadata['Рассылка']['time'], 1) > 10*60:
        text = 'ТЫ не просто позорище, ты еще и ленивое позорище! Отвечай быстрее'

    await callback.answer(text=text,show_alert=True)
    fullname = callback.from_user.full_name
    user_id = str(callback.from_user.id)

    ACTIVE_SESSION[callback.from_user.id] = False

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
    
    


    gif = FSInputFile("assets/cat.gif") #Тут меняешь на название своей гифки
    await callback.message.answer_animation(animation=gif)
    await callback.answer() 
 
@dp.message(Command("losers_list"))
async def losers_list(message: Message):
    losers_data = {}
    if os.path.exists("databases/losers.json"):
        with open("databases/losers.json", "r", encoding="utf-8") as f:
            losers_data = json.load(f)
    if not losers_data:
            await message.answer("✨ Список пока пуст.")
            return

    # 1. Сортируем по количеству отказов (от большего к меньшему)
    sorted_losers = sorted(losers_data.items(),reverse=True)

    # 2. Формируем красивый текст
    text = "📊 **ОФИЦИАЛЬНЫЙ РЕЙТИНГ ПОЗОРА:**\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, info) in enumerate(sorted_losers):
        rank = medals[i] if i < 3 else "🔹"
        name = info['name']
        count = info['count']
        
        # Добавляем строку в список
        text += f"{rank} `{name}` — {count} раз(а)\n"

        loser_gif = FSInputFile("assets/deathNote.gif")

        await bot.send_animation(message.chat.id, animation=loser_gif, caption=text, parse_mode="Markdown")
        return
    else:
        peacedog = FSInputFile("assets/peacedog.webp")
        await message.answer_photo(photo=peacedog,caption="Список предателей пока пуст. Либо все идут гулять, либо ты еще никому не писал! 😇")

poll_storage: dict[str, dict[int, list[int]]] = {}

# Хранилище: poll_id → вопрос и варианты
poll_meta: dict[str, dict] = {}


@dp.message(F.text, StateFilter(WaitForMessage.create_pool))
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
        await message.answer_photo(photo=cry, caption="Либо ты не добавил ID друзей в list_members либо у тебя их нет...")
        return 

    builder = InlineKeyboardBuilder() 
    builder.add(InlineKeyboardButton( 
        text=btn1_text, 
        callback_data="yes",
        style="success") 
    ) 
    builder.add(InlineKeyboardButton( 
        text=btn2_text, 
        callback_data="no",
        style="danger") 
    )  
      
    await message.answer("Запускаю рассылку...\n Чтобы посмотреть список тех кто отказался: /losers_list") 
    metadata = {f"Рассылка": 
        {
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
        await bot.send_photo(chat_id=member_id, photo=mem, caption=user_text, reply_markup=builder.as_markup())
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

        # Сохраняем метаданные опроса
        poll_storage[poll_id] = {}
        poll_meta[poll_id] = {
            "question": sent.poll.question,
            "options": options,
            "chat_id": message.chat.id,
        }

        await message.answer(f"Опрос создан. ID: `{poll_id}`")

@dp.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    poll_id    = poll_answer.poll_id
    user_id    = poll_answer.user.id
    username   = poll_answer.user.username or "Unknown"
    option_ids = poll_answer.option_ids

    # Пользователь отозвал голос — пустой список
    if not option_ids:
        poll_storage.get(poll_id, {}).pop(user_id, None)
        print(f"@{username} отозвал голос в опросе {poll_id}")
        return

    # Сохраняем голос
    if poll_id not in poll_storage:
        poll_storage[poll_id] = {}

    poll_storage[poll_id][user_id] = option_ids

    # Получаем текст выбранных вариантов
    meta    = poll_meta.get(poll_id, {})
    options = meta.get("options", [])
    chosen  = [options[i] for i in option_ids if i < len(options)]

    await bot.send_message(
        chat_id=user_id,
        text=f"✅ Ваш ответ записан: {', '.join(chosen)}"
    )


@dp.callback_query(F.data == 'pool_results')
async def show_results(callback: CallbackQuery):
    """Показывает результаты всех опросов."""
    if not poll_storage:
        await callback.message.answer("Нет данных об опросах.")
        return

    text = "📊 Результаты опросов:\n\n"

    for poll_id, votes in poll_storage.items():
        meta    = poll_meta.get(poll_id, {})
        options = meta.get("options", [])
        question = meta.get("question", poll_id)

        # Подсчёт голосов по вариантам
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


@dp.message(StateFilter(WaitForMessage.wait_msg, WaitForMessage.wait_btn1, WaitForMessage.wait_btn2, WaitForMessage.create_pool))
async def cancel_msg(message: Message):
    await message.answer("Отправить можно только текст :(")

async def main(): 
    try: 
        await dp.start_polling(bot) 
    finally: 
        await bot.session.close() 
 
if __name__ == '__main__': 
    asyncio.run(main())