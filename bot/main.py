from nextcord.ext import commands
from lib.common import parse_config
from bot.commands import TimerManager

bot = commands.Bot(command_prefix='rem ')
config = parse_config('discord')

@bot.event
async def on_ready():
    print('------------------')
    print(f'bot ready {bot.user.name}')
    print('------------------')


bot.add_cog(TimerManager(bot))
bot.run(config['token'])