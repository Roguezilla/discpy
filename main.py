import os
from dotenv import load_dotenv

from discpy import DiscPy
from message import Message
from embeds import EmbedBuilder
from events import ReactionAddEvent, ReadyEvent
from stardb import StarDB

load_dotenv()

bot = DiscPy(os.getenv('TOKEN'), ',')
db = StarDB('db.db')

@bot.register_event
async def on_ready(self: DiscPy, ready: ReadyEvent):
		print(f'->Logged in as {ready.user.username}')
		await self.update_presence('with stars.', self.ActivityType.WATCHING, self.Status.DND)

@bot.register_event
async def on_message(self: DiscPy, msg: Message):
	print(f'-Author: {msg.author.username}\n-Content: {msg.content}')

	if msg.content == 'poggers':
		self.send_message(msg.channel_id, 'poggers indeed')

@bot.register_event
async def on_reaction_add(self, reaction: ReactionAddEvent):
	if not db.get_server(reaction.guild_id) or db.is_archived(reaction.guild_id, reaction.channel_id, reaction.message_id):
		return

	if db.get_server(reaction.guild_id)['archive_emote'] == str(reaction.emoji):
		message = Message(self.get_message(reaction.channel_id, reaction.message_id))
		
		emote_match = list(filter(lambda r: str(r.emoji) == db.get_server(reaction.guild_id)['archive_emote'], message.reactions))
		channel_count = db.get_custom_count(reaction.guild_id, reaction.channel_id)
		needed_count = channel_count['amount'] if channel_count else db.get_server(reaction.guild_id)['archive_emote_amount']
		
		if emote_match and emote_match[0].count >= needed_count:
			print('hai!')

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