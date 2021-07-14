import os
from dotenv import load_dotenv

from discpy import DiscPy

load_dotenv()

bot = DiscPy(os.getenv('TOKEN'))
bot.start()