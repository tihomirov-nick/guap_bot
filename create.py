from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

storage = MemoryStorage()

bot = Bot(token=('6306742274:AAElH9FtIPEsJFD0DDqOyjEPU3pNpDyVHZU'))
dp = Dispatcher(bot, storage=storage)