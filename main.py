import os
from dotenv import load_dotenv

from discpy import Bot

load_dotenv()

bot = Bot(os.getenv('TOKEN'))
bot.start()