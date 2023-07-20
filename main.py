from aiogram import types
from aiogram.utils import executor
import asyncio

from datetime import datetime, time, timedelta
import sqlite3 as sq

from create import dp
from handlers import client, admin
from database import database

async def scheduler():
    while True:
        now = datetime.now().time()

        if str(now.strftime('%H:%M')) == '00:00':
            with open('data.db', 'rb') as file:
                await dp.bot.send_document(-902831076, file)

        for user_id, send_time in await database.get_all_from_users():
            send_time = datetime.strptime(send_time, '%H:%M').time()
            if now.strftime('%H:%M') == send_time.strftime('%H:%M'):
                days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                tomorrow = datetime.now() + timedelta(days=1)
                day_of_week = days_of_week[tomorrow.weekday()]
                group = await database.get_group_by_id(user_id)
                rasp = client.get_rasp(day_of_week, group)
                formatted_schedule = client.format_schedule_future(rasp, day_of_week)
                await dp.bot.send_message(user_id, formatted_schedule)
                
        await asyncio.sleep(60)


async def on_startup(dp):
    database.sql_start()
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота")])
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())


client.register_handlers_client(dp)
admin.register_handlers_admin(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
