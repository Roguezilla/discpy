from message import Message
import os
from dotenv import load_dotenv

from discpy import DiscPy
from embeds import EmbedBuilder
from events import ReactionAddEvent, ReadyEvent

load_dotenv()

bot = DiscPy(os.getenv('TOKEN'), ',')

@bot.register_event
async def on_ready(self: DiscPy, ready: ReadyEvent):
		await self.update_presence('with stars.', self.ActivityType.WATCHING, self.Status.DND)

@bot.register_event
async def on_message(self: DiscPy, msg: Message):
	print(f'-Author: {msg.author.username}\n-Content: {msg.content}')

	if msg.content == 'poggers':
		self.send_message(msg.channel_id, 'poggers indeed')

@bot.register_event
async def on_reaction_add(self, reaction: ReactionAddEvent):
		message = Message(self.get_message(reaction.channel_id, reaction.message_id))
		print(f'-Emoji: {reaction.emoji.format()}\n-Count: {message.get_reaction(reaction.emoji).count}')

@bot.register_command()
async def ping(self: DiscPy, msg: Message):
	self.send_message(msg.channel_id, 'Pong.')

@bot.register_command()
async def embed(self: DiscPy, msg: Message):
	embed = EmbedBuilder(title='Title', description='Description.', url='https://www.google.com/', color=0xffcc00)
	embed.set_author(name='rogue', url='https://www.google.com/', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_image(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_thumbnail(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.set_footer(text='by rogue#0001', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
	embed.add_field(name='yes', value='<#777251828743143424>', inline=True)
	embed.add_field(name='no', value='no', inline=True)
	embed.add_field(name='maybe', value='<@212149701535989760>', inline=False)

	self.send_message(msg.channel_id, embed=embed.embed_dict)

bot.start()