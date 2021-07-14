class EmbedBuilder:
    def __init__(self, title = '', description = '', url = '', color = None):
        self.embed_dict = {
            'title': title,
            'type': 'rich',
            'description': description,
            'url': url,
            'timestamp': None,
            'color': color,
            'fields': []
        }
    
    def set_footer(self, text, icon_url = ''):
        self.embed_dict['footer'] = {
            'text': text,
            'icon_url': icon_url
        }

    def set_image(self, url):
        self.embed_dict['image'] = {
            'url': url
        }

    def set_thumbnail(self, url):
        self.embed_dict['thumbnail'] = {
            'url': url
        }
    
    def set_author(self, name = '', url = '', icon_url = ''):
        self.embed_dict['author'] = {
            'name': name,
            'url': url,
            'icon_url': icon_url
        }

    def add_field(self, name, value, inline):
        self.embed_dict['fields'].append({
            'name': name,
            'value': value,
            'inline': inline
        })