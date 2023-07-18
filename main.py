from aiogram import types
from aiogram.utils import executor
import asyncio

from datetime import datetime, time, timedelta
import sqlite3 as sq

import requests
from bs4 import BeautifulSoup
from collections import defaultdict

from create import dp
from handlers import client
from database import database


def format_schedule(text: str, day: str) -> str:
    lines = text.split('\n')
    formatted_text = f'Расписание на завтра:\n\n☀️ {day}\n'
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


async def scheduler():
    while True:
        now = datetime.now().time()
        conn = sq.connect('data.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, send_time TEXT)')
        conn.commit()
        for user_id, send_time in c.execute('SELECT * FROM users'):
            send_time = datetime.strptime(send_time, '%H:%M').time()
            if now.strftime('%H:%M') == send_time.strftime('%H:%M'):
                days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                tomorrow = datetime.now() + timedelta(days=1)
                day_of_week = days_of_week[tomorrow.weekday()]
                group = c.execute('SELECT "group" FROM groups WHERE id = ?', (user_id,)).fetchone()[0]
                print(group)
                rasp = get_rasp(day_of_week, group)
                formatted_schedule = format_schedule(rasp, day_of_week)
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
