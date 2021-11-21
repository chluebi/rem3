import nextcord
from lib.common import parse_config
from lib import database
from bot.util import parse_message
from bot.commands import execute_command
from bot.trigger_timer import main_loop

client = nextcord.Client()
config = parse_config('discord')
db_connection = database.connect()


@client.event
async def on_ready():
    print('------------------')
    print(f'bot ready {client.user.name}')
    print('------------------')
    await main_loop(client, db_connection)


@client.event
async def on_message(message):
    p_message = parse_message(message.content)
    if p_message is not None:
        await execute_command(client, message, p_message, db_connection)

client.run(config['token'])