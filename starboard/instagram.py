from requests import get

from discpy import DiscPy
from dataset import Database
from message import Message
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
	if 'edge_sidecar_to_children' not in data:
		# if data doesn't have media_metadata, then it's not a gallery
		return 0

	gallery_cache[str(msg.channel.id) + str(msg.id)] = {
		'size': len(data['edge_sidecar_to_children']['edges']),
		'curr': 1
	}

	for i in range(len(data['edge_sidecar_to_children']['edges'])):
		gallery_cache[str(msg.channel.id) + str(msg.id)][i + 1] = data['edge_sidecar_to_children']['edges'][i]['node']['display_url']

	# when repopulating, we need to match the current picture with its index
	if repopulate:
		url = msg.embeds[0].image.__getattribute__('url')
		for key in gallery_cache[str(msg.channel.id) + str(msg.id)]:
			if gallery_cache[str(msg.channel.id) + str(msg.id)][key] == url:
				gallery_cache[str(msg.channel.id) + str(msg.id)]['curr'] = key

class Instagram:
	def __init__(self, bot, db):
		self.bot: DiscPy = bot
		self.db: Database = db

	@staticmethod
	def url_data(url):
		# cut out useless stuff and form an api url
		url = url.split("?")[0]
		api_url = url + '?__a=1'
		return get(api_url, headers = {'User-agent': 'discpy'}).json()['graphql']['shortcode_media']

	@staticmethod
	def return_link(url, msg=None):
		data = Instagram.url_data(url)
		# only galeries have media_metadata
		if 'edge_sidecar_to_children' in data:
			# thankfully edge_sidecar_to_children has the images in the right order
			ret = data['edge_sidecar_to_children']['edges'][0]['node']['display_url']
			# as the link is a gallery, we need to populate the gallery cache
			if msg: populate_cache(data, msg)
		else:
			ret = data['display_url']
		return ret

	async def on_message(self, msg: Message):
		pass

	async def on_reaction_add(self, reaction: ReactionAddEvent):
		pass