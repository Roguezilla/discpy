from json.decoder import JSONDecodeError
import requests
import websockets
import asyncio
import json
import platform

from definitions import ActivityType, OpCodes, Status

class Bot:
	def __init__(self, token):
		self.__token = token
		self.loop = asyncio.get_event_loop()
		self.__BASE_API_URL = 'https://discord.com/api/v9'
		self.__sequence = None
		self.__socket = None
		self.debug = 1
		self.ready = False

	def __get_gateway(self):
		return requests.get(url = self.__BASE_API_URL + '/gateway', headers = { 'Authorization': f'Bot {self.__token}' }).json()['url'] + '/?v=9&encoding=json'

	def __identify_json(self, intents):
		return json.dumps({
			"op": OpCodes.IDENTIFY,
			"d": {
				"token": self.__token,
				"intents": intents, #32509 = basically all of them but the that need toggling options on dashboard
				"properties": {
					"$os": platform.system(),
					"$browser": "discpy",
					"$device": "discpy"
				}
			}
		})

	def send_message(self, channel_id, content):
		requests.post(
			self.__BASE_API_URL + f'/channels/{channel_id}/messages',
			headers = { 'Authorization': f'Bot {self.__token}', 'Content-Type': 'application/json', 'User-Agent': 'discpy' },
			data = json.dumps ( { "content": content } )
		)

	async def update_presence(self, name, type: ActivityType, status: Status):
		presence = {
			"op": OpCodes.PRESENCE,
			"d": {
				"since": None,
				"activities": [{
					"name": name,
					"type": type
				}],
				"status": status,
				"afk": False
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
				print("Sent OpCodes.HEARTBEAT")

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
							await self.__socket.send(self.__identify_json(intents=32509))
								
							if self.debug:
								print("Sent OpCodes.IDENTIFY")
								
						elif op == OpCodes.HEARTBEAT_ACK:
							if self.debug:
								print("Got OpCodes.HEARTBEAT_ACK")

						elif op == OpCodes.HEARTBEAT:
							payload = {
								'op': OpCodes.HEARTBEAT,
								'd': self.__sequence
							}

							await self.__socket.send(json.dumps(payload))

							if self.debug:
								print("Forced OpCodes.HEARTBEAT")

					event = recv_json['t']
					if event == 'READY':
						self.ready = True
						if self.debug:
							print('READY')

						await self.on_ready()

				except JSONDecodeError:
					print('JSONDecodeError')

	def start(self):
		self.loop.create_task(self.__process_payloads())
		self.loop.run_forever()

	async def on_ready(self):
		await self.update_presence("with stars.", ActivityType.watching, Status.do_not_disturb)
		self.send_message(777254114581020673, "discpy represent")