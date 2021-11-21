from nextcord.ext import commands
import nextcord
from lib.common import parse_config
from bot.commands import TimerManager

intents = nextcord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='rem ', intents=intents)
config = parse_config('discord')

@bot.event
async def on_ready():
    print('------------------')
    print(f'bot ready {bot.user.name}')
    print('------------------')


bot.add_cog(TimerManager(bot), description='Manages the reminder/timer setting and triggering of said timers')
bot.run(config['token'])