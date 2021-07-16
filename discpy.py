from json.decoder import JSONDecodeError
from typing import Callable
import requests
import websockets
import asyncio
import json
import platform

from events import ReactionAddEvent, ReadyEvent
from message import Message

class DiscPy:
	class OpCodes:
		DISPATCH = 0
		HEARTBEAT = 1
		IDENTIFY = 2
		PRESENCE = 3
		VOICE_STATE = 4
		VOICE_PING = 5
		RESUME = 6
		RECONNECT = 7
		REQUEST_MEMBERS = 8
		INVALIDATE_SESSION = 9
		HELLO = 10
		HEARTBEAT_ACK = 11
		GUILD_SYNC = 12

	class Status:
		ONLINE = 'online'
		OFFLINE = 'offline'
		IDLE = 'idle'
		DND = 'dnd'
		INVISIBLE = 'invisible'

	class ActivityType:
		UNKNOWN = -1
		PLAYING = 0
		STREAMING = 1
		LISTENING = 2
		WATCHING = 3
		CUSTOM = 4
		COMPETING = 5

	class Intents:
		GUILDS = (1 << 0)
		"""
		- GUILD_CREATE
		- GUILD_UPDATE
		- GUILD_DELETE
		- GUILD_ROLE_CREATE
		- GUILD_ROLE_UPDATE
		- GUILD_ROLE_DELETE
		- CHANNEL_CREATE
		- CHANNEL_UPDATE
		- CHANNEL_DELETE
		- CHANNEL_PINS_UPDATE
		- THREAD_CREATE
		- THREAD_UPDATE
		- THREAD_DELETE
		- THREAD_LIST_SYNC
		- THREAD_MEMBER_UPDATE
		- THREAD_MEMBERS_UPDATE *
		- STAGE_INSTANCE_CREATE
		- STAGE_INSTANCE_UPDATE
		- STAGE_INSTANCE_DELETE
		"""

		GUILD_MEMBERS = (1 << 1)
		"""
		- GUILD_MEMBER_ADD
		- GUILD_MEMBER_UPDATE
		- GUILD_MEMBER_REMOVE
		- THREAD_MEMBERS_UPDATE *
		"""

		GUILD_BANS = (1 << 2)
		"""
		- GUILD_BAN_ADD
		- GUILD_BAN_REMOVE
		"""

		GUILD_EMOJIS = (1 << 3)
		"""
		- GUILD_EMOJIS_UPDATE
		"""

		GUILD_INTEGRATIONS = (1 << 4)
		"""
		- GUILD_INTEGRATIONS_UPDATE
		- INTEGRATION_CREATE
		- INTEGRATION_UPDATE
		- INTEGRATION_DELETE
		"""

		GUILD_WEBHOOKS = (1 << 5)
		"""
		- WEBHOOKS_UPDATE
		"""

		GUILD_INVITES = (1 << 6)
		"""
		- INVITE_CREATE
		- INVITE_DELETE
		"""

		GUILD_VOICE_STATES = (1 << 7)
		"""
		- VOICE_STATE_UPDATE
		"""

		GUILD_PRESENCES = (1 << 8)
		"""
		- PRESENCE_UPDATE
		"""

		GUILD_MESSAGES = (1 << 9)
		"""
		- MESSAGE_CREATE
		- MESSAGE_UPDATE
		- MESSAGE_DELETE
		- MESSAGE_DELETE_BULK
		"""

		GUILD_MESSAGE_REACTIONS = (1 << 10)
		"""
		- MESSAGE_REACTION_ADD
		- MESSAGE_REACTION_REMOVE
		- MESSAGE_REACTION_REMOVE_ALL
		- MESSAGE_REACTION_REMOVE_EMOJI
		"""

		GUILD_MESSAGE_TYPING = (1 << 11)
		"""
		- TYPING_START
		"""

		DIRECT_MESSAGES = (1 << 12)
		"""
		- MESSAGE_CREATE
		- MESSAGE_UPDATE
		- MESSAGE_DELETE
		- CHANNEL_PINS_UPDATE
		"""

		DIRECT_MESSAGE_REACTIONS = (1 << 13)
		"""
		- MESSAGE_REACTION_ADD
		- MESSAGE_REACTION_REMOVE
		- MESSAGE_REACTION_REMOVE_ALL
		- MESSAGE_REACTION_REMOVE_EMOJI
		"""

		DIRECT_MESSAGE_TYPING = (1 << 14)
		"""
		- TYPING_START
		"""

	def __init__(self, token, prefix):
		self.__token = token
		self.__prefix = prefix
		self.loop = asyncio.get_event_loop()
		self.__socket = None
		self.__BASE_API_URL = 'https://discord.com/api/v9'

		self.__sequence = None

		self.bot: ReadyEvent = None

		self.debug = 1

		self.__commands = {}

	def __get_gateway(self):
		return requests.get(url = self.__BASE_API_URL + '/gateway', headers = { 'Authorization': f'Bot {self.__token}' }).json()['url'] + '/?v=9&encoding=json'

	def __log(self, str):
		if self.debug:
			print(str)

	def __hearbeat_json(self):
		return json.dumps({
			'op': self.OpCodes.HEARTBEAT,
			'd': self.__sequence
		})

	def __identify_json(self, intents):
		return json.dumps({
			'op': self.OpCodes.IDENTIFY,
			'd': {
				'token': self.__token,
				'intents': intents, #32509 = basically all of them but the ones that need toggling options on the dashboard
				'properties': {
					'$os': platform.system(),
					'$browser': 'discpy',
					'$device': 'discpy'
				}
			}
		})
	
	def __resume_json(self):
		return json.dumps({
			'op': self.OpCodes.RESUME,
			'd': {
				'seq': self.__sequence,
				'session_id': self.bot.session_id,
				'token': self.__token
			}
		})

	def register_command(self):
		def decorator(func: Callable):
			self.__commands[f'{self.__prefix}{func.__name__}'] = func
			self.__log(f'Registed command: {func.__name__}')

		return decorator

	def is_command(self, start):
		return start in self.__commands

	def register_event(self, event: Callable):
		setattr(self, event.__name__, event)
		self.__log(f'Registed event: {event.__name__}')

	async def update_presence(self, name, type: ActivityType, status: Status):
		presence = {
			'op': self.OpCodes.PRESENCE,
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
				'op': self.OpCodes.HEARTBEAT,
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
					if op != self.OpCodes.DISPATCH:
						print(f'OpCode: {op}')
						if op == self.OpCodes.HELLO:
							self.loop.create_task(self.__do_heartbeats(recv_json['d']['heartbeat_interval']))
							# GUILD_MESSAGES + GUILD_MESSAGE_REACTIONS 
							await self.__socket.send(self.__identify_json(intents=self.Intents.GUILD_MESSAGES | self.Intents.GUILD_MESSAGE_REACTIONS))
								
							if self.debug:
								print('Sent OpCodes.IDENTIFY')
								
						elif op == self.OpCodes.HEARTBEAT_ACK:
							self.__log('Got OpCodes.HEARTBEAT_ACK')

						elif op == self.OpCodes.HEARTBEAT:
							await self.__socket.send(self.__hearbeat_json())

							self.__log('Forced OpCodes.HEARTBEAT')

						elif op == self.OpCodes.RECONNECT:
							self.__log('Got OpCodes.RECONNECT')

							self.__socket.send(self.__resume_json())

							self.__log('Sent OpCodes.RESUME')
						else:
							self.__log(f'Got unhanled OpCode: {op}')
					else:
						event = recv_json['t']
						if event == 'READY':
							self.__log('READY')

							self.bot = ReadyEvent(recv_json['d'])

							if hasattr(self, 'on_ready'):
								await getattr(self, 'on_ready')(self, self.bot)
						
						elif event == 'RESUMED':
							self.__log('RESUMED')

						elif event == 'MESSAGE_CREATE':
							await self.__on_message(Message(recv_json['d']))

						elif event == 'MESSAGE_REACTION_ADD':
							if hasattr(self, 'on_reaction_add'):
								await getattr(self, 'on_reaction_add')(self, ReactionAddEvent(recv_json['d']))

					if self.debug:
						print(f'Sequence: {self.__sequence}')

				except JSONDecodeError:
					print('JSONDecodeError')

	def start(self):
		self.loop.create_task(self.__process_payloads())
		self.loop.run_forever()

	async def __on_message(self, msg: Message):		
		split = msg.content.split(' ')
		if self.is_command(split[0]) and msg.author.id != self.bot.user.id:
			await self.__commands[msg.content.split(" ")[0]](self, msg, *split[1:])

		if hasattr(self, 'on_message'):
			await getattr(self, 'on_message')(self, msg)

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