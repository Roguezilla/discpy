import re

import dataset
from requests import get
from requests_oauthlib import OAuth1
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup

from discpy import DiscPy
from events import ReactionAddEvent
from message import Message
from embeds import EmbedBuilder
from starboard.reddit import Reddit
from starboard.instagram import Instagram

class Starboard:
	def __init__(self, db) -> None:
		self.db = dataset.connect(f'sqlite:///{db}')
		self.__exceptions = dict()
		self.__twitter_auth = OAuth1(self.db['twitter'].find_one(name='api_key')['value'], self.db['twitter'].find_one(name='api_secret')['value'],
									self.db['twitter'].find_one(name='access_token')['value'], self.db['twitter'].find_one(name='access_token_secret')['value'])

	async def on_reaction_add(self, bot: DiscPy, reaction: ReactionAddEvent):
		if not self.__get_server(reaction.guild_id) or self.__is_archived(reaction.guild_id, reaction.channel_id, reaction.message_id):
			return

		if self.__get_server(reaction.guild_id)['archive_emote'] == str(reaction.emoji):
			message = bot.fetch_message(reaction.channel_id, reaction.message_id)
			message.guild_id = reaction.guild_id
			
			emote_match = list(filter(lambda r: str(r.emoji) == self.__get_server(reaction.guild_id)['archive_emote'], message.reactions))
			channel_count = self.__get_custom_count(reaction.guild_id, reaction.channel_id)
			needed_count = channel_count['amount'] if channel_count else self.__get_server(reaction.guild_id)['archive_emote_amount']
			
			if emote_match and emote_match[0].count >= needed_count:
				await self.__do_archival(bot, message)

	def __get_server(self, id):
		return self.db['server'].find_one(server_id = id)

	def __get_custom_count(self, server_id, channel_id):
		return self.db['custom_count'].find_one(server_id = server_id, channel_id = channel_id)

	def __is_archived(self, server_id, channel_id, message_id):
		return self.db['ignore_list'].find_one(server_id = server_id, channel_id = channel_id, message_id = message_id)

	async def __do_archival(self, bot: DiscPy, msg: Message):
		embed_info = await self.__build_info(msg)
		if not embed_info:
			return

		embed = EmbedBuilder(color=0xffcc00)

		if embed_info['custom_author']:
			embed.set_author(name=f'{embed_info["custom_author"].username}', icon_url=f'{embed_info["custom_author"].avatar_url}')
		else:
			embed.set_author(name=f'{msg.author.username}', icon_url=f'{msg.author.avatar_url}')
			
		if embed_info['content']:
			embed.add_field(name='What?', value=embed_info['content'], inline=False)

		embed.add_field(name='Where?', value=f'<#{msg.channel_id}>', inline=True)
		embed.add_field(name='Where exactly?', value=f'[Jump!](https://discordapp.com/channels/{msg.guild_id}/{msg.channel_id}/{msg.id})', inline=True)

		if embed_info['flag'] == 'image' and embed_info['image_url']:
			embed.set_image(url=embed_info['image_url'])

		embed.set_footer(text="by rogue#0001")

		bot.send_message(channel_id=self.__get_server(msg.guild_id)['archive_channel'], embed=embed.embed_dict)

		if embed_info['flag'] == 'video':
			bot.send_message(channel_id=self.__get_server(msg.guild_id)['archive_channel'], content=embed_info['image_url'])

		self.db['ignore_list'].insert(dict(server_id = msg.guild_id, channel_id = msg.channel_id, message_id = msg.id))

	async def __build_info(self, msg: Message):
		info = {}

		def __get_id(url):
			u_pars = urlparse(url)
			quer_v = parse_qs(u_pars.query).get('v')
			if quer_v:
				return quer_v[0]
			pth = u_pars.path.split('/')
			if pth:
				return pth[-1]

		def set_info(flag='', content='', image_url='', custom_author=''):
			info['flag'] = flag
			info['content'] = content
			info['image_url'] = image_url
			info['custom_author'] = custom_author

		# good ol' regex
		url = re.findall(
			r"((?:https?):(?://)+(?:[\w\d_.~\-!*'();:@&=+$,/?#[\]]*))", msg.content)

		if f'{msg.guild_id}{msg.channel_id}{msg.id}' in self.__exceptions:
			set_info(
				'image',
				msg.content,
				self.__exceptions.pop(f'{msg.guild_id}{msg.channel_id}{msg.id}')
			)
		else:
			# tldr, someone might want to override the image
			if url and not msg.attachments:
				if 'deviantart.com' in url[0] or 'tumblr.com' in url[0] or 'pixiv.net' in url[0]:
					processed_url = get(url[0].replace('mobile.', '')).text
					set_info(
						'image',
						f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
						BeautifulSoup(processed_url, 'html.parser').find('meta', attrs={'property': 'og:image'}).get('content')
					)
				elif 'www.instagram.com' in url[0]:
					set_info(
						'image',
						f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
						Instagram.return_link(url[0])
					)
				elif 'twitter.com' in url[0]:
					# fuck twitter
					tweet_id = re.findall(r'https://twitter\.com/.*?/status/(\d*)', url[0].replace('mobile.', ''))
					r = get(f'https://api.twitter.com/1.1/statuses/show.json?id={tweet_id[0]}&tweet_mode=extended', auth=self.__twitter_auth).json()
					if 'media' in r['entities']:
						set_info(
							'image',
							f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
							r['entities']['media'][0]['media_url']
						)	
					else:
						set_info(
							'message',
							msg.content
						)
				elif 'reddit.com' in url[0] or 'redd.it' in url[0]:
					set_info(
						'image',
						f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
						Reddit.return_link(url[0])
					)
				elif 'youtube.com' in url[0] or 'youtu.be' in url[0]:
					set_info(
						'image',
						f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
						f'https://img.youtube.com/vi/{__get_id(url[0])}/0.jpg'
					)
				elif 'dcinside.com' in url[0]:
					set_info(
						'image',
						f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
						msg.attachments[0].url
					)
				elif 'imgur' in url[0]:
					if 'i.imgur' not in url[0]:
						processed_url = get(url[0].replace('mobile.', '')).text
						set_info(
							'image',
							f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
							BeautifulSoup(processed_url, 'html.parser').find('meta', attrs={'property': 'og:image'}).get('content').replace('?fb', '')
						)
					else:
						set_info(
							'image',
							msg.content.replace(url[0], "").strip(),
							url[0]
						)
				elif 'https://tenor.com' in url[0]:
					processed_url = get(url[0].replace('mobile.', '')).text
					for img in BeautifulSoup(processed_url, 'html.parser').findAll('img', attrs={'src': True}):
						if 'media1.tenor.com' in img.get('src'):
							set_info(
								'image',
								f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
								img.get('src')
							)
				elif any(ext in url[0] for ext in ['.mp4', '.mov', '.webm']):
					set_info(
						'video',
						f'[The video below](https://youtu.be/dQw4w9WgXcQ)\n{msg.content.replace(url[0], "").strip()}',
						url[0]
					)
				elif 'discordapp.com' in url[0] or 'twimg.com' in url[0]:
					set_info(
						'image',
						msg.content.replace(url[0], '').strip(),
						msg.embeds[0].url
					)
				else:
					# high chance that it's the actual image
					if msg.embeds and msg.embeds[0].url != url[0]:
						set_info(
							'image',
							f'[Source]({url[0]})\n{msg.content.replace(url[0], "").strip()}',
							msg.embeds[0].url
						)
					else:
						set_info(
							'message',
							msg.content,
						)
			else:
				if msg.attachments:
					file = msg.attachments[0]
					is_video = any(ext in msg.attachments[0].url for ext in ['.mp4', '.mov', '.webm'])
					set_info(
						'video' if is_video else 'image',
						f'{msg.content}\n[{"Video spoiler alert!" if is_video else "Spoiler alert!"}]({msg.attachments[0].url})' if file.is_spoiler
							else (f'[The video below](https://youtu.be/dQw4w9WgXcQ)\n{msg.content}' if is_video else msg.content),
						'' if file.is_spoiler else msg.attachments[0].url
					)
				else:
					if msg.embeds:
						if any(x in msg.embeds[0].description for x in ['instagram.com', 'reddit.com', 'redd.it']):
							content = msg.embeds[0].description.split('\n')
							set_info(
								'image',
								'\n'.join(content[1:]) if len(content) > 1 else '',
								msg.embeds[0].image.__getattribute__('url'),
								await self.fetch_user(int(msg.embeds[0].fields[0].__dict__['value'][2:len(msg.embeds[0].fields[0].__dict__['value'])-1]))
							)
					else:
						set_info(
							'message',
							msg.content,
						)

		return info