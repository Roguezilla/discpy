import re
import asyncio
from requests import get

from discpy import DiscPy
from dataset import Database
from message import Message, Embed
from events import ReactionAddEvent

"""
'msgid': {
	'size': 2,
	'curr': 1,
	'1': 'url',
	'2': 'url'
}
"""
gallery_cache = dict()

def populate_cache(data, msg: Message, repopulate=False):
	if 'media_metadata' not in data:
		# if data doesn't have media_metadata, then it's not a gallery
		return 0

	gallery_cache[str(msg.channel_id) + str(msg.id)] = {
		'size': len(data['gallery_data']['items']),
		'curr': 1
	}

	for i in range(len(data['gallery_data']['items'])):
		idx = data['gallery_data']['items'][i]['media_id']
		gallery_cache[str(msg.channel_id) + str(msg.id)][i + 1] = data['media_metadata'][idx]['s']['u'].replace('&amp;', '&')

	# when repopulating, we need to match the current picture with its index
	if repopulate:
		url = msg.embeds[0].image.__getattribute__('url')
		for key in gallery_cache[str(msg.channel_id) + str(msg.id)]:
			if gallery_cache[str(msg.channel_id) + str(msg.id)][key] == url:
				gallery_cache[str(msg.channel_id) + str(msg.id)]['curr'] = key

class Reddit:
	def __init__(self, bot, db):
		self.bot: DiscPy = bot
		self.db: Database = db

	@staticmethod
	def url_data(url):
		# cut out useless stuff and form an api url
		url = url.split("?")[0]
		api_url = url + '.json'
		return get(api_url, headers = {'User-agent': 'discpy'}).json()[0]['data']['children'][0]['data']

	@staticmethod
	def return_link(url, msg=None):
		data = Reddit.url_data(url)
		# only galeries have media_metadata
		if 'media_metadata' in data:
			# media_metadata is unordered, gallery_data has the right order
			first = data['gallery_data']['items'][0]['media_id']
			# the highest quality pic always the last one
			ret = data['media_metadata'][first]['s']['u'].replace('&amp;', '&')
			# as the link is a gallery, we need to populate the gallery cache
			if msg: populate_cache(data, msg)
		else:
			# covers gifs
			ret = data['url_overridden_by_dest']
			# the url doesn't end with any of these then the post is a video, so fallback to the thumbnail
			if '.jpg' not in ret and '.png' not in ret and '.gif' not in ret:
				ret = data['preview']['images'][0]['source']['url'].replace('&amp;', '&')
		
		return (ret, data["title"])

	async def on_message(self, bot: DiscPy, msg: Message):
		if msg.author.bot:
			return

		if self.db['server'].find_one(server_id = msg.guild_id)['reddit_embed']:
			url = re.findall(r"(\|{0,2}<?[<|]*(?:https?):(?://)+(?:[\w\d_.~\-!*'();:@&=+$,/?#[\]]*)\|{0,2}>?)", msg.content)
			if url and ('reddit.com' in url[0] or 'redd.it' in url[0]) and not (url[0].startswith('<') and url[0].endswith('>')) and not (url[0].startswith('||') and url[0].endswith('||')):
				url[0] = url[0].replace('<', '').replace('>', '').replace('|', '')
				image, title = self.return_link(url[0], msg)
				if image:
					embed = Embed(title = title, description = f'[Jump to directly reddit]({url[0]})\n{msg.content.replace(url[0], "").strip()}', color=0xffcc00)
					embed.set_image(url=image)
					embed.add_field(name='Sender', value=msg.author.mention, inline=True)

					sent: Message = bot.send_message(msg.channel_id, embed=embed.as_json())

					if str(msg.channel_id) + str(msg.id) in gallery_cache:
						# copy old message info into the new message(our embed) and delete old message from the dictionary
						gallery_cache[str(sent.channel_id) + str(sent.id)] = gallery_cache[str(msg.channel_id) + str(msg.id)]
						del gallery_cache[str(msg.channel_id) + str(msg.id)]

						embed: Embed = sent.embeds[0]
						embed.add_field(name='Page', value=f"{gallery_cache[str(sent.channel_id) + str(sent.id)]['curr']}/{gallery_cache[str(sent.channel_id) + str(sent.id)]['size']}", inline=True)
						bot.edit_message(sent, embed = embed.as_json())
						
						bot.add_reaction(sent, '⬅️')
						# le ratelimit
						await asyncio.sleep(0.1)
						bot.add_reaction(sent, '➡️')

					# we don't really the message and it only occupies space now
					bot.delete_message(msg)

	async def on_reaction_add(self, bot: DiscPy, reaction: ReactionAddEvent):
		pass