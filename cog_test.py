from discpy import DiscPy, Message

class TestCog(DiscPy.Cog):	
	def __init__(self, bot: DiscPy):
		@bot.event(self)
		async def on_message(ctx: DiscPy, event: Message):
			await ctx.send_message(event.channel_id, 'cog on_message')

		@bot.command()
		async def cog(ctx: DiscPy, event: Message):
			await ctx.send_message(event.channel_id, 'cog command')

class TestCog2(DiscPy.Cog):	
	def __init__(self, bot: DiscPy):
		@bot.event(self)
		async def on_message(ctx: DiscPy, event: Message):
			await ctx.send_message(event.channel_id, 'cog2 on_message')

		@bot.command()
		async def cog2(ctx: DiscPy, event: Message):
			await ctx.send_message(event.channel_id, 'cog2 command')