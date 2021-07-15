from datetime import datetime
from typing import List

from websockets import auth

class MentionedUser:
    def __init__(self, mention):
        self.username = mention['username']
        self.public_flags = mention['public_flags']
        self.roles = mention['member']['roles']
        self.mute = mention['member']['mute']
        self.joined_at = datetime.fromisoformat(mention['member']['joined_at'])
        self.hoisted_role = mention['member']['hoisted_role']
        self.deaf = mention['member']['deaf']
        self.id = mention['id']
        self.discriminator = mention['discriminator']
        self.avatar_url = f'https://cdn.discordapp.com/avatars/{self.id}/{mention["avatar"]}'

def test(dict, key):
    return dict[key] if key in dict else None

class Author:
    def __init__(self, member, author):
        self.username = author['username']
        self.id = author['id']
        self.discriminator = author['discriminator']
        self.avatar_url = f'https://cdn.discordapp.com/avatars/{self.id}/{author["avatar"]}'

        self.bot = test(author, 'bot')
        self.system = test(author, 'system')
        self.mfa_enabled = test(author, 'mfa_enabled')
        self.locale = test(author, 'locale')
        self.verified = test(author, 'verified')
        self.email = test(author, 'email')
        self.flags = test(author, 'flags')
        self.premium_type = test(author, 'premium_type')
        self.public_flags = test(author, 'public_flags')

        if member is not None:
            self.roles = member['roles']
            self.mute = member['mute']
            self.joined_at = datetime.fromisoformat(member['joined_at'])
            self.hoisted_role = member['hoisted_role']
            self.deaf = member['deaf']

class Attachment:
    def __init__(self, attachment):
        self.width = test(attachment, 'width')
        self.url = attachment['url']
        self.size = attachment['size']
        self.proxy_url = attachment['proxy_url']
        self.id = attachment['id']
        self.height = test(attachment, 'height')
        self.filename = attachment['filename']
        self.content_type = test(attachment, 'content_type')

class Emoji:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def format(self):
        return f'<:{self.name}:{self.id}>'

    def __eq__(self, o):
        return self.id == o.id and self.name == o.name

class Reaction:
    def __init__(self, reaction) -> None:
        self.emoji = Emoji(reaction['emoji']['id'], reaction['emoji']['name'])
        self.count = reaction['count']
        self.me = reaction['me']

class Message:
    def __init__(self, msg):
        self.type = msg['type']
        self.tts = msg['tts']
        self.timestamp = datetime.fromisoformat(msg['timestamp'])
        self.referenced_message = msg['referenced_message'] if 'referenced_message' in msg else None
        self.pinned = msg['pinned']
        self.nonce = test(msg, 'nonce')

        self.mentions = []
        for user in msg['mentions']:
            self.mentions.append(MentionedUser(user))

        self.mention_roles = msg['mention_roles']
        self.mention_everyone = msg['mention_everyone']
        self.author = Author(test(msg, 'member'), msg['author'])
        self.id = msg['id']
        self.flags = msg['flags']
        self.embeds = msg['embeds']
        self.edited_timestamp = None if msg['edited_timestamp'] == None else datetime.fromisoformat(msg['edited_timestamp'])
        self.content = msg['content']
        self.components = msg['components']
        self.channel_id = msg['channel_id']
        self.guild_id = test(msg, 'guild_id')

        self.attachments = []
        for attachment in msg['attachments']:
            self.attachments.append(Attachment(attachment))

        self.reactions = []
        if 'reactions' in msg:
            for reaction in msg['reactions']:
                self.reactions.append(Reaction(reaction))

    def get_reaction(self, emoji: Emoji) -> Reaction:
        for reaction in self.reactions:
            if reaction.emoji == emoji:
                return reaction
