import json

def parse_config(name):
	with open(f'configs/{name}_config.json', 'r+') as f:
		data = json.load(f)
	return data


def get_message_link(guild_id, channel_id, message_id, receiver_id):
	if guild_id == 0:
		created_message_link = f'https://discordapp.com/channels/@me/{channel_id}/{message_id}'
	elif message_id == 0:
		created_message_link = 'Timer created in Web.'
	else:
		created_message_link = f'https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}'
	return created_message_link


def get_channel_link(guild_id, channel_id):
	return f'https://discordapp.com/channels/{guild_id}/{channel_id}'