import json
from lib.common import parse_config, get_message_link
from bot import embeds

import asyncio
from discord import DMChannel, TextChannel

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


def get_relative_timestamp(seconds):
	return f'<t:{seconds}:R>'

def get_absolute_timestamp(seconds):
	return f'<t:{seconds}:F>'


async def success_message(embed, ctx):
	try:
		await ctx.message.add_reaction('✅')
	except Exception as e:
		pass

	try:
		message = await ctx.send(embed=embed)
	except Exception as e:
		pass
	else:
		if not is_dm(ctx.channel):
			ctx.bot.loop.create_task(delete_message(message, 10))

async def info_message(embed, ctx):
	try:
		message = await ctx.send(embed=embed)
	except Exception as e:
		await ctx.author.send(embed=embed)
		await ctx.message.add_reaction('🆗')

async def error_message(embed, ctx, delete=True):
	try:
		await ctx.message.add_reaction('❌')
	except Exception as e:
		pass

	try:
		message = await ctx.send(embed=embed)
	except Exception as e:
		message_link = get_message_link(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id)
		embed.add_field(name='Triggered from different channel', value='Triggered from [this message]({0})'.format(message_link))
		await ctx.author.send(embed=embed)
	else:
		if not is_dm(ctx.channel) and delete:
			ctx.bot.loop.create_task(delete_message(message, 15))
			

async def delete_message(message, seconds):
	await asyncio.sleep(seconds)
	await message.delete()