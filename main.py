import os

from dotenv import load_dotenv

from discpy import DiscPy
from message import Message, Embed
from events import ReactionAddEvent, ReadyEvent
from starboard.starboard import Starboard
from starboard.reddit import Reddit
from starboard.instagram import Instagram

load_dotenv()

bot = DiscPy(os.getenv('TOKEN'), ',')
sb = Starboard('db.db')

ig = Instagram(bot, sb.db)
reddit = Reddit(bot, sb.db)

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
	await ig.on_message(self, msg)
	await reddit.on_message(self, msg)

@bot.register_event
async def on_reaction_add(self: DiscPy, reaction: ReactionAddEvent):
	await sb.on_reaction_add(self, reaction)
	await ig.on_reaction_add(self, reaction)
	await reddit.on_reaction_add(self, reaction)
	
"""
Commands
"""
@bot.register_command
async def ping(self: DiscPy, msg: Message):
	self.send_message(msg.channel_id, 'Pong.')

@bot.register_command
async def embed(self: DiscPy, msg: Message):
	embed = Embed(title='Title', description='Description.', url='https://www.google.com/', color=0xffcc00)
	embed.set_author(name='rogue', url='https://www.google.com/', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_image(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_thumbnail(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_footer(text='by rogue#0001', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.add_field(name='yes', value='<#777251828743143424>', inline=True)
	embed.add_field(name='no', value='no', inline=True)
	embed.add_field(name='maybe', value='<@212149701535989760>', inline=False)

	self.send_message(msg.channel_id, embed=embed.as_json())

bot.start()