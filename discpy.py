from json.decoder import JSONDecodeError
import requests
import websockets
import asyncio
import json
import platform

from definitions import ActivityType, OpCodes, Status
from reaction_events import ReactionAddEvent
from message import Message
from embeds import EmbedBuilder

class DiscPy:
	def __init__(self, token):
		self.__token = token
		self.loop = asyncio.get_event_loop()
		self.__socket = None
		self.__BASE_API_URL = 'https://discord.com/api/v9'

		self.__sequence = None
		self.__session_id = None

		self.debug = 1
		self.ready = False

	def __get_gateway(self):
		return requests.get(url = self.__BASE_API_URL + '/gateway', headers = { 'Authorization': f'Bot {self.__token}' }).json()['url'] + '/?v=9&encoding=json'

	def __hearbeat_json(self):
		return json.dumps({
			'op': OpCodes.HEARTBEAT,
			'd': self.__sequence
		})

	def __identify_json(self, intents):
		return json.dumps({
			'op': OpCodes.IDENTIFY,
			'd': {
				'token': self.__token,
				'intents': intents, #32509 = basically all of them but the that need toggling options on dashboard
				'properties': {
					'$os': platform.system(),
					'$browser': 'discpy',
					'$device': 'discpy'
				}
			}
		})
	
	def __resume_json(self):
		return json.dumps({
			'op': OpCodes.RESUME,
			'd': {
                'seq': self.__sequence,
                'session_id': self.__session_id,
                'token': self.__token
            }
		})

	def send_message(self, channel_id, content = '', embed = None):		
		if not content and not embed:
			return

		return requests.post(
			self.__BASE_API_URL + f'/channels/{channel_id}/messages',
			headers = { 'Authorization': f'Bot {self.__token}', 'Content-Type': 'application/json', 'User-Agent': 'discpy' },
			data = json.dumps ( {'content': content, 'embeds': [embed] if embed else None} )
		)

	def get_message(self, channel_id, message_id):
		return requests.get(
			self.__BASE_API_URL + f'/channels/{channel_id}/messages/{message_id}',
			headers = { 'Authorization': f'Bot {self.__token}', 'Content-Type': 'application/json', 'User-Agent': 'discpy' }
		).json()

	async def update_presence(self, name, type: ActivityType, status: Status):
		presence = {
			'op': OpCodes.PRESENCE,
			'd': {
				'since': None,
				'activities': [{
					'name': name,
					'type': type
				}],
				'status': status,
				'afk': False
			}
		}
		await self.__socket.send(json.dumps(presence))

	async def __do_heartbeats(self, interval):
		while True:
			payload = {
				'op': OpCodes.HEARTBEAT,
				'd': self.__sequence
			}
			await self.__socket.send(json.dumps(payload))

			if self.debug:
				print('Sent OpCodes.HEARTBEAT')

			await asyncio.sleep(delay=interval / 1000)

	async def __process_payloads(self):
		async with websockets.connect(self.__get_gateway()) as self.__socket:
			while True:
				raw_recv = await self.__socket.recv()
				try:
					recv_json = json.loads(raw_recv)

					if recv_json['s'] is not None:
						self.__sequence = recv_json['s']
					
					op = recv_json['op']
					if op != OpCodes.DISPATCH:
						if op == OpCodes.HELLO:
							self.loop.create_task(self.__do_heartbeats(recv_json['d']['heartbeat_interval']))
							# GUILD_MESSAGES + GUILD_MESSAGE_REACTIONS 
							await self.__socket.send(self.__identify_json(intents=(1 << 9) | (1 << 10)))
								
							if self.debug:
								print('Sent OpCodes.IDENTIFY')
								
						elif op == OpCodes.HEARTBEAT_ACK:
							if self.debug:
								print('Got OpCodes.HEARTBEAT_ACK')

						elif op == OpCodes.HEARTBEAT:
							await self.__socket.send(self.__hearbeat_json())

							if self.debug:
								print('Forced OpCodes.HEARTBEAT')

						elif op == OpCodes.RECONNECT:
							if self.debug:
								print('Got OpCodes.RECONNECT')

							self.__socket.send(self.__resume_json())

							if self.debug:
								print('Sent OpCodes.RESUME')
						else:
							if self.debug:
								print(f'Got unhanled OpCode: {op}')
					else:
						event = recv_json['t']
						if event == 'READY':
							self.ready = True
							if self.debug:
								print('READY')

							self.__session_id = recv_json['d']['session_id']

							await self.__on_ready()
						elif event == 'RESUMED':
							print('RESUMED')
						elif event == 'MESSAGE_CREATE':
							await self.__on_message(Message(recv_json['d']))
						elif event == 'MESSAGE_REACTION_ADD':
							await self.__on_reaction_add(ReactionAddEvent(recv_json['d']))

					if self.debug:
						print(f'Sequence: {self.__sequence}')

				except JSONDecodeError:
					print('JSONDecodeError')

	def start(self):
		self.loop.create_task(self.__process_payloads())
		self.loop.run_forever()

	async def __on_ready(self):
		await self.update_presence('with stars.', ActivityType.watching, Status.do_not_disturb)

	# maybe try to make something like commands?
	async def __on_message(self, msg: Message):
		print(f'-Author: {msg.author.username}\n-Content: {msg.content}')

		if msg.content.startswith(',ping'):
			self.send_message(msg.channel_id, content='Pong.')

		if msg.content.startswith(',embed'):
			embed = EmbedBuilder(title='Title', description='Description.', url='https://www.google.com/', color=0xffcc00)
			embed.set_author(name='rogue', url='https://www.google.com/', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
			embed.set_image(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
			embed.set_thumbnail(url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
			embed.set_footer(text='by rogue#0001', icon_url='https://cdn.discordapp.com/emojis/700809695933497355.gif')
			embed.add_field(name='yes', value='<#777251828743143424>', inline=True)
			embed.add_field(name='no', value='no', inline=True)
			embed.add_field(name='maybe', value='<@212149701535989760>', inline=False)

			self.send_message(msg.channel_id, embed=embed.embed_dict)

	async def __on_reaction_add(self, reaction: ReactionAddEvent):
		message = Message(self.get_message(reaction.channel_id, reaction.message_id))
		print(f'-Emoji: {reaction.emoji.format()}\n-Count: {message.get_reaction(reaction.emoji).count}')