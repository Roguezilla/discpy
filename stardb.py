import dataset

class StarDB:
    def __init__(self, db) -> None:
        self.__db = dataset.connect(f'sqlite:///{db}')

    def get_server(self, id):
	    return self.__db['server'].find_one(server_id = id)

    def get_custom_count(self, server_id, channel_id):
        return self.__db['custom_count'].find_one(server_id = server_id, channel_id = channel_id)

    def is_archived(self, server_id, channel_id, message_id):
        return self.__db['ignore_list'].find_one(server_id = server_id, channel_id = channel_id, message_id = message_id)    