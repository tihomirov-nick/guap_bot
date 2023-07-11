from aiogram import types
from aiogram.utils import executor

from create import dp
from handlers import client
from database import database


async def on_startup(dp):
    database.sql_start()
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота")])

client.register_handlers_client(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


# Функционал
# # # - Поиск по преподам, группе, предмету, расписание
# - Рассылка + заметки
# - Загрузка файлов, поиск через Inline
# - Расписание сессии, рассылка перед экзаменом
