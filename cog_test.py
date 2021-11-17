import asyncio

from discpy import DiscPy, Message

class TestCog(DiscPy.Cog):	
	def __init__(self, bot: DiscPy):
		@bot.event(self)
		async def on_message(ctx: DiscPy, msg: Message):
			await ctx.send_message(msg.channel_id, 'cog on_message')

		@bot.command()
		async def cog(ctx: DiscPy, msg: Message):
			await ctx.send_message(msg.channel_id, 'cog command')
