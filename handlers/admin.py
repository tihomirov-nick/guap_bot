from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import database as db
from create import bot
import os

ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Клава админа, открывается после ввода /admin
async def admin_start(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id == ADMIN_ID:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="Загрузить файл", callback_data="Загрузить"), InlineKeyboardButton(text="Удалить файл", callback_data="Удалить"))
        await bot.send_message(message.from_user.id, text=f"{message.from_user.first_name}, вы успешно авторизовались как администратор!", reply_markup=main_kb)

async def cal_admin_start(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.from_user.id == ADMIN_ID:
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="Загрузить файл", callback_data="Загрузить"), InlineKeyboardButton(text="Удалить файл", callback_data="Удалить"))
        await callback.message.edit_text(text=f"{callback.from_user.first_name}, вы успешно авторизовались как администратор!", reply_markup=main_kb)


# Upload file
class AddFile(StatesGroup):
    file = State()

async def admin_upload_file(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.from_user.id == ADMIN_ID:
        upload_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Главная"))
        await callback.message.edit_text(text="Пожалуйста, отправьте мне файл для загрузки", reply_markup=upload_kb)
        await AddFile.file.set()

async def admin_upload_file_message(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        file_id = message.document.file_id
        file_name = message.document.file_name
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="Загрузить файл", callback_data="Загрузить"), InlineKeyboardButton(text="Удалить файл", callback_data="Удалить"))
        if await db.file_exists(file_name):
            await message.answer(f"Файл с именем '{file_name}' уже существует в базе данных. Загрузка отменена 🥺", reply_markup=main_kb)
        else:
            await db.add_file(file_id, file_name)
            await message.answer(f"Файл '{file_name}' успешно загружен ❤️", reply_markup=main_kb)
        await state.finish()

# Delete file
class DeleteFile(StatesGroup):
    name = State()

async def admin_delete_file(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if callback.from_user.id == ADMIN_ID:
        delete_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="🔙 Назад", callback_data="Главная"))
        await callback.message.edit_text(text="Пожалуйста, отправьте мне имя файла, который нужно удалить из базы данных", reply_markup=delete_kb)
        await DeleteFile.name.set()

async def admin_delete_file_message(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        file_name = message.text
        main_kb = InlineKeyboardMarkup() \
            .add(InlineKeyboardButton(text="Загрузить файл", callback_data="Загрузить"), InlineKeyboardButton(text="Удалить файл", callback_data="Удалить"))
        if await db.file_exists(file_name):
            await db.delete_file(file_name)
            await message.answer(f"Файл '{file_name}' успешно удален из базы данных 💔", reply_markup=main_kb)
        else:
            await message.answer(f"Файл с именем '{file_name}' не найден в базе данных. Удаление отменено 🥺", reply_markup=main_kb)
        await state.finish()

def register_handlers_admin(dp: Dispatcher):
    # Menu
    dp.register_message_handler(admin_start, commands=['admin'], state='*')
    dp.register_callback_query_handler(cal_admin_start, lambda c:c.data == "Главная", state='*')
   
    # Upload
    dp.register_callback_query_handler(admin_upload_file, lambda c: c.data == "Загрузить")
    dp.register_message_handler(admin_upload_file_message,content_types=['document'], state=AddFile.file)
    
    # Delete
    dp.register_callback_query_handler(admin_delete_file, lambda c: c.data == "Удалить")
    dp.register_message_handler(admin_delete_file_message, state=DeleteFile.name)
