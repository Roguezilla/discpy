import os

from dotenv import load_dotenv

from discpy import DiscPy
from message import Message, Embed
from events import ReactionAddEvent, ReadyEvent
from cog_test import TestCog, TestCog2
import perms

load_dotenv()

bot = DiscPy(os.getenv('TOKEN'), debug=1)

"""
Events
"""
@bot.event()
async def on_ready(self: DiscPy, event: ReadyEvent):
	print(f'->Logged in as {event.user.username}')
	await self.update_presence('with stars.', self.ActivityType.WATCHING, self.Status.DND)

@bot.event()
async def on_message(self: DiscPy, event: Message):
	await self.send_message(event.channel_id, 'on_message')

@bot.event()
async def on_reaction_add(self: DiscPy, event: ReactionAddEvent):
	pass
	
"""
Commands
"""
@bot.command()
@bot.permissions(perms.basic_perms_check)
async def ping(self: DiscPy, msg: Message):
	await self.send_message(msg.channel_id, 'Pong.')

@bot.command()
@bot.permissions(perms.basic_perms_check2)
async def ping2(self: DiscPy, msg: Message):
	await self.send_message(msg.channel_id, 'Pong2.')

@bot.command()
async def embed(self: DiscPy, msg: Message):
	embed = Embed(title='Title', description='Description.', url='https://www.google.com/', color=0xffcc00)
	embed.set_author(name='rogue', url='https://www.google.com/', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_image(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_thumbnail(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_footer(text='by rogue#0001', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.add_field(name='yes', value='<#777251828743143424>', inline=True)
	embed.add_field(name='no', value='no', inline=True)
	embed.add_field(name='maybe', value='<@212149701535989760>', inline=False)

	await self.send_message(msg.channel_id, embed=embed.as_json())

TestCog(bot)
TestCog2(bot)

bot.start()
