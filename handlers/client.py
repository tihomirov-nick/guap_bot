from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import asyncio
import sqlite3
from datetime import datetime, time

from database import database
from create import bot


async def command_start(message: types.Message, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
        .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔍 Поиск", callback_data="Поиск"))
    await bot.send_message(message.from_user.id, text=f"👋🏻 Привет, {message.from_user.first_name}! Я твой личный бот-помощник с расписанием занятий.\n\nЯ готов помочь тебе организовать твою учебную неделю. Просто спроси меня о расписании, и я предоставлю тебе актуальную информацию о занятиях, датах, времени и месте проведения.\n\nТы также можешь попросить меня обновить расписание, если оно изменилось. Удачи с твоими занятиями!", reply_markup=main_kb)


async def cal_command_start(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
        .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔍 Поиск", callback_data="Поиск"))
    await callback.message.edit_text(text=f"👋🏻 Привет, {callback.from_user.first_name}! Я твой личный бот-помощник с расписанием занятий.\n\nЯ готов помочь тебе организовать твою учебную неделю. Просто спроси меня о расписании, и я предоставлю тебе актуальную информацию о занятиях, датах, времени и месте проведения.\n\nТы также можешь попросить меня обновить расписание, если оно изменилось. Удачи с твоими занятиями!", reply_markup=main_kb)


# Groups
async def group(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    group = await database.get_group(callback.from_user.id)
    if group:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="👥 Изменить группу", callback_data="Изменить группу"), InlineKeyboardButton(text="🏡 Домой", callback_data="Домой"))
        await callback.message.edit_text(text=f"Твоя группа: {await database.get_group(callback.from_user.id)}", reply_markup=main_kb)
    else:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="👥 Ввести группу", callback_data="Ввести группу"), InlineKeyboardButton(text="🏡 Домой", callback_data="Домой"))
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
        InlineKeyboardButton(text="🏡 Домой", callback_data="Домой")
    )
    await message.answer(f"Ты успешно ввел номер группы!\nТвоя группа: {await database.get_group(message.from_user.id)}", reply_markup=main_kb)
    await state.finish()


# Sending
async def start_cmd_handler(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    for hour in range(24):
        for minute in [0, 30]:
            send_time = time(hour, minute)
            keyboard.add(InlineKeyboardButton(send_time.strftime('%H:%M'), callback_data=send_time.strftime('%H:%M')))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Привет! Выбери время из списка ниже и я буду ежедневно отправлять тебе сообщение в это время.", reply_markup=keyboard)


async def callback_query_handler(callback_query: types.CallbackQuery):
    if callback_query.data == 'Рассылка':
        return
    try:
        send_time = datetime.strptime(callback_query.data, '%H:%M').time()
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, send_time TEXT)')
        conn.commit()
        c.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (callback_query.from_user.id, send_time.strftime('%H:%M')))
        conn.commit()
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, f"Окей, я буду отправлять тебе сообщение каждый день в {send_time.strftime('%H:%M')}. Чтобы изменить время рассылки, нажми на кнопку 'Рассылка' еще раз.")
    except ValueError:
        pass


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
    dp.register_callback_query_handler(cal_command_start, lambda c: c.data == "Домой", state='*')

    dp.register_callback_query_handler(group, lambda c: c.data == "Группа", state='*')
    dp.register_callback_query_handler(set_group, lambda c: c.data == "Ввести группу")
    dp.register_message_handler(set_group_message, state=AddGroup.group)

    dp.register_callback_query_handler(change_group, lambda c: c.data == "Изменить группу")
    dp.register_message_handler(change_group_message, state=ChangeGroup.group)

    dp.register_callback_query_handler(start_cmd_handler, lambda c: c.data == 'Рассылка', state='*')
    dp.register_callback_query_handler(callback_query_handler, state='*')
