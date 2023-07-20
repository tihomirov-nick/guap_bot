from datetime import datetime, time
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InlineQueryResultCachedDocument
import sqlite3 as sq
import hashlib
from collections import defaultdict
import requests
from bs4 import BeautifulSoup

from database import database
from create import bot


def format_schedule_future(text: str, day: str) -> str:
    lines = text.split('\n')
    formatted_text = f'Расписание на завтра:\n\n☀️ {day}\n'
    for line in lines:
        if 'пара' in line:
            time = line.split(')')[0] + ')'
            formatted_text += f'\n🕘 {time}\n'
        else:
            formatted_text += f'{line}\n'
    return formatted_text


def format_schedule(text: str, day: str) -> str:
    lines = text.split('\n')
    formatted_text = f'Расписание на сегодня:\n\n☀️ {day}\n'
    for line in lines:
        if 'пара' in line:
            time = line.split(')')[0] + ')'
            formatted_text += f'\n🕘 {time}\n'
        else:
            formatted_text += f'{line}\n'
    return formatted_text


def get_rasp(send_day, group):
    url = f'https://guap.ru/rasp'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    option = soup.find('option', string=str(group))
    value = option['value']
    url = f'https://guap.ru/rasp/?g={value}'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    schedule = defaultdict(list)
    current_day = None

    found_h3 = False
    for tag in soup.find_all(['h3', 'h4', 'span']):
        if tag.name == 'h3':
            found_h3 = True
            current_day = tag.text
        elif found_h3:
            schedule[current_day].append(tag.text)

    text = ''

    for day, lessons in schedule.items():
        if str(day) == str(send_day):
            for lesson in lessons:
                text += '\n' + lesson

    return text

async def command_start(message: types.Message, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
        .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔍 Поиск", switch_inline_query_current_chat="Афанасьева"))
    await bot.send_message(message.from_user.id, text=f"👋🏻 Привет, {message.from_user.first_name}! Я твой личный бот-помощник с расписанием занятий.\n\nЯ готов помочь тебе организовать твою учебную неделю. Просто спроси меня о расписании, и я предоставлю тебе актуальную информацию о занятиях, датах, времени и месте проведения.\n\nТы также можешь попросить меня обновить расписание, если оно изменилось. Удачи с твоими занятиями!", reply_markup=main_kb)


async def cal_command_start(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
        .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔍 Поиск", switch_inline_query_current_chat="Афанасьева"))
    await callback.message.edit_text(text=f"👋🏻 Привет, {callback.from_user.first_name}! Я твой личный бот-помощник с расписанием занятий.\n\nЯ готов помочь тебе организовать твою учебную неделю. Просто спроси меня о расписании, и я предоставлю тебе актуальную информацию о занятиях, датах, времени и месте проведения.\n\nТы также можешь попросить меня обновить расписание, если оно изменилось. Удачи с твоими занятиями!", reply_markup=main_kb)


# Inline
async def inline_query(query: types.InlineQuery):
    base = sq.connect('data.db')
    cur = base.cursor()
    search_query = query.query
    if search_query != '':
        cur.execute("SELECT * FROM files WHERE name LIKE ? OR description LIKE ?", ('%' + search_query + '%', '%' + search_query + '%',))
        results = []
        for row in cur.fetchall():
            file_id = row[1]
            file_name = row[2]
            description = row[3]
            result_id = hashlib.md5(file_id.encode()).hexdigest()  # уникальный идентификатор результата
            results.append(InlineQueryResultCachedDocument(
                id=result_id,
                title=file_name,
                description=description,
                document_file_id=file_id,
            ))
        if len(results) > 0:
            await query.answer(results)
        else:
            await query.answer(
                results=[InlineQueryResultArticle(
                    id='no_results',
                    title='Поиск файлов',
                    description='Не удалось найти файлы',
                    input_message_content=types.InputTextMessageContent(message_text='Не удалось найти файлы')
                )]
            )

# Schedule
async def rasp(callback_query: types.CallbackQuery):
    days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    tomorrow = datetime.now()
    day_of_week = days_of_week[tomorrow.weekday()]
    group = await database.get_group_by_id(callback_query.from_user.id)
    rasp = get_rasp(day_of_week, group)
    formatted_schedule = format_schedule(rasp, day_of_week)
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Домой"))
    await callback_query.message.edit_text(text=formatted_schedule, reply_markup=main_kb)


# Sender
async def start_cmd_handler(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    for hour in range(20,24):
        send_time = time(hour, 0)
        keyboard.add(InlineKeyboardButton(send_time.strftime('%H:%M'), callback_data=send_time.strftime('%H:%M')))
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="Домой"))
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text(text="Привет! Выбери время из списка ниже и я буду ежедневно отправлять тебе сообщение в это время.", reply_markup=keyboard)


async def callback_query_handler(callback_query: types.CallbackQuery):
    if callback_query.data == 'Рассылка':
        return
    try:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
            .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔍 Поиск", switch_inline_query_current_chat="Афанасьева"))
        send_time = datetime.strptime(callback_query.data, '%H:%M').time()
        conn = sq.connect('data.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, send_time TEXT)')
        conn.commit()
        c.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (callback_query.from_user.id, send_time.strftime('%H:%M')))
        conn.commit()
        await bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_text(text=f"Окей, я буду отправлять тебе сообщение каждый день в {send_time.strftime('%H:%M')}. Чтобы изменить время рассылки, нажми на кнопку 'Рассылка' еще раз.", reply_markup=main_kb)
    except ValueError:
        pass


# Groups
async def group(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    group = await database.get_group(callback.from_user.id)
    if group:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="👥 Изменить группу", callback_data="Изменить группу"), InlineKeyboardButton(text="🔙 Назад", callback_data="Домой"))
        await callback.message.edit_text(text=f"Твоя группа: {await database.get_group(callback.from_user.id)}", reply_markup=main_kb)
    else:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="👥 Ввести группу", callback_data="Ввести группу"), InlineKeyboardButton(text="🔙 Назад", callback_data="Домой"))
        await callback.message.edit_text(text="Похоже ты здесь впервые! У тебя пока что не указан номер группы!", reply_markup=main_kb)


class AddGroup(StatesGroup):
    group = State()


async def set_group(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Группа"))
    await callback.message.edit_text(text="Отправь номер своей группы", reply_markup=main_kb)
    await AddGroup.group.set()


async def set_group_message(message: types.Message, state: FSMContext):
    group = message.text
    await database.set_group_in_db(message.from_user.id, group)
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Изменить группу", callback_data="Изменить группу"), InlineKeyboardButton(text="🏡 Домой", callback_data="Домой"))
    await message.answer(f"Ты успешно ввел номер группы!\nТвоя группа: {await database.get_group(message.from_user.id)}", reply_markup=main_kb)
    await state.finish()


class ChangeGroup(StatesGroup):
    group = State()


async def change_group(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    back_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(text="🔙 Назад", callback_data="Группа"))
    await callback.message.edit_text(text="Отправь номер своей группы", reply_markup=back_kb)
    await ChangeGroup.group.set()


async def change_group_message(message: types.Message, state: FSMContext):
    group = message.text
    await database.change_group_in_db(message.from_user.id, group)
    main_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="👥 Изменить группу", callback_data="Изменить группу"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="Домой")
    )
    await message.answer(f"Ты успешно ввел номер группы!\nТвоя группа: {await database.get_group(message.from_user.id)}", reply_markup=main_kb)
    await state.finish()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
    dp.register_callback_query_handler(cal_command_start, lambda c: c.data == "Домой", state='*')
    
    # Groups handlers
    dp.register_callback_query_handler(group, lambda c: c.data == "Группа", state='*')
    dp.register_callback_query_handler(set_group, lambda c: c.data == "Ввести группу")
    dp.register_message_handler(set_group_message, state=AddGroup.group)

    dp.register_callback_query_handler(change_group, lambda c: c.data == "Изменить группу")
    dp.register_message_handler(change_group_message, state=ChangeGroup.group)

    # Inline handler
    dp.register_inline_handler(inline_query)

    # Schedule handlers
    dp.register_callback_query_handler(rasp, lambda c: c.data == "Расписание", state='*')

    # Sender handlers
    dp.register_callback_query_handler(start_cmd_handler, lambda c: c.data == 'Рассылка', state='*')
    dp.register_callback_query_handler(callback_query_handler, state='*')
