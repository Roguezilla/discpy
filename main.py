import os

from dotenv import load_dotenv

from discpy import DiscPy
from message import Message
from events import ReactionAddEvent, ReadyEvent
from starboard.main import Starboard

load_dotenv()

bot = DiscPy(os.getenv('TOKEN'), ',')
sb = Starboard('db.db')
exceptions = dict()

"""
Events
"""
@bot.register_event
async def on_ready(self: DiscPy, ready: ReadyEvent):
		print(f'->Logged in as {ready.user.username}')
		await self.update_presence('with stars.', self.ActivityType.WATCHING, self.Status.DND)

@bot.register_event
async def on_message(self: DiscPy, msg: Message):
	pass

@bot.register_event
async def on_reaction_add(self: DiscPy, reaction: ReactionAddEvent):
	await sb.on_reaction_add(self, reaction)

"""
Commands
"""
@bot.register_command
async def ping(self: DiscPy, msg: Message):
	self.send_message(msg.channel_id, 'Pong.')

bot.start()