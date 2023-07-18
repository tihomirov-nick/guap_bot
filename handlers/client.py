from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import database
from create import bot

async def command_start(message: types.Message, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
        .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔎 Поиск", callback_data="Поиск"))
    await bot.send_message(message.from_user.id, text=f"👋🏻 Привет, {message.from_user.first_name}! Я твой личный бот-помощник с расписанием занятий.\n\nЯ готов помочь тебе организовать твою учебную неделю. Просто спроси меня о расписании, и я предоставлю тебе актуальную информацию о занятиях, датах, времени и месте проведения.\n\nТы также можешь попросить меня обновить расписание, если оно изменилось. Удачи с твоими занятиями!", reply_markup=main_kb)


async def cal_command_start(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    main_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="👥 Группа", callback_data="Группа"), InlineKeyboardButton(text="📅 Расписание", callback_data="Расписание")) \
        .add(InlineKeyboardButton(text="✉️ Рассылка", callback_data="Рассылка"), InlineKeyboardButton(text=f"🔎 Поиск", callback_data="Поиск"))
    await callback.message.edit_text(text=f"👋🏻 Привет, {callback.from_user.first_name}! Я твой личный бот-помощник с расписанием занятий.\n\nЯ готов помочь тебе организовать твою учебную неделю. Просто спроси меня о расписании, и я предоставлю тебе актуальную информацию о занятиях, датах, времени и месте проведения.\n\nТы также можешь попросить меня обновить расписание, если оно изменилось. Удачи с твоими занятиями!", reply_markup=main_kb)

# Поиск


async def search(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    search_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="🔎 Классический поиск", callback_data="Классический поиск"), InlineKeyboardButton(text="🔎 Inline-поиск", callback_data="Инлайн поиск")) \
        .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Домой"))
    await callback.message.edit_text(text="Выберите режим для поиска файлов:", reply_markup=search_kb)

class Search(StatesGroup):
    search_file = State()

async def search_classic_mode(callback: types.CallbackQuery, state: FSMContext):
    back_kb = InlineKeyboardMarkup() \
        .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Поиск"))
    await callback.message.edit_text(text="Введите ключевые слова для поиска:", reply_markup=back_kb)
    await Search.search_file.set()

async def search_classic_mode_message(message: types.Message, state: FSMContext):
    keywords = message.text
    files = await database.search_files_in_db(keywords)
    if files:
        # Если найдены файлы, отобразите их информацию и клавиатуру с вариантами действий
        for file in files:
            file_info = f"Имя файла: {file['name']}\nОписание: {file['description']}"
            file_kb = InlineKeyboardMarkup() \
                .add(InlineKeyboardButton(text="Скачать файл", callback_data=f"Скачать,{file['name']}"), 
                     InlineKeyboardButton(text="Следующий файл", callback_data="Следующий")) \
                .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Поиск"))
            await message.answer(file_info, reply_markup=file_kb)
    else:
        await state.finish()
        back_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="🔁 Повторить", callback_data="Классический поиск"), \
                 InlineKeyboardButton(text="🔙 Назад", callback_data="Поиск"))
        await message.answer("Файлы не найдены", reply_markup=back_kb)


# Группы
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



async def get_photo_id(message: types.Message):
    file_id = message.photo[0].file_id
    await bot.send_message(message.from_user.id, text=file_id)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state='*')
    dp.register_callback_query_handler(cal_command_start, lambda c: c.data == "Домой", state='*')
   
    #Поиск
    dp.register_callback_query_handler(search, lambda c: c.data == "Поиск", state='*')
    dp.register_callback_query_handler(search_classic_mode, lambda c: c.data == "Классический поиск")
    dp.register_message_handler(search_classic_mode_message, state=Search.search_file)

    #Группы
    dp.register_callback_query_handler(group, lambda c: c.data == "Группа", state='*')
    dp.register_callback_query_handler(set_group, lambda c: c.data == "Ввести группу")
    dp.register_message_handler(set_group_message, state=AddGroup.group)

    dp.register_callback_query_handler(change_group, lambda c: c.data == "Изменить группу")
    dp.register_message_handler(change_group_message, state=ChangeGroup.group)

    dp.register_message_handler(get_photo_id, content_types=['photo'])
