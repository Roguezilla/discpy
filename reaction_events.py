from message import Author, Emoji

class ReactionAddEvent:
    def __init__(self, event):
        self.user_id = event['user_id']
        self.message_id = event['message_id']
        self.author = Author(event['member'], event['member']['user'])
        self.emoji = Emoji(event['emoji']['id'], event['emoji']['name'])
        self.channel_id = event['channel_id']
        self.guild_id = event['guild_id']