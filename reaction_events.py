from message import Emoji, Member

class ReactionAddEvent:
	def __init__(self, event):
		self.user_id = event['user_id']
		self.message_id = event['message_id']
		self.author = Member(event['member']['user'], event['member'])
		self.emoji = Emoji(event['emoji'])
		self.channel_id = event['channel_id']
		self.guild_id = event['guild_id']