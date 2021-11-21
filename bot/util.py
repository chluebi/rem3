import json
from lib.common import parse_config

from nextcord import DMChannel, TextChannel

config = parse_config('discord')

def parse_message(content):
	l = len(config['prefix'])
	if content[:l] != config['prefix']:
		return None

	content = content[l:]
	if len(content) < 1:
		return None
	if content[0] == ' ':
		content = content[1:]

	msg = ['']
	quotes = False
	for i, letter in enumerate(content):
		if not quotes:
			if letter == ' ':
				msg.append('')
			elif letter in ['`', '“', '\"', '„', '\''] and letter in content[i+1:]:
				quotes = letter
				if len(msg[-1]) > 0:
					msg.append('')
			else:
				msg[-1] += letter
		else:
			if (quotes == '“' and letter == '”') \
				or (quotes == '„' and letter == '“') \
				or (quotes == letter and letter in '`\"\''):
				quotes = False
			else:
				msg[-1] += letter

	return msg


def is_dm(channel):
	return isinstance(channel, DMChannel)