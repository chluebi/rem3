import logging
import traceback

from nextcord.ext import commands
import nextcord

from lib.common import parse_config
from bot.commands import TimerManager
import bot.embeds as embeds

config = parse_config('discord')

intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='{0} '.format(config['prefix']), intents=intents)

logging.basicConfig(handlers=[logging.FileHandler('bot.log', 'a', encoding='utf-8')], format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@bot.event
async def on_ready():
    print('------------------')
    print(f'bot ready {bot.user.name}')
    print('------------------')

@bot.event
async def on_command_error(ctx, error):
    error_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    if (isinstance(error, nextcord.ext.commands.CommandNotFound)):
        return

    if (isinstance(error, nextcord.ext.commands.CheckFailure)):
        return

    m = f'''Internal error:
```{error}```

Probably contact Lu'''
    await ctx.message.add_reaction('❌')
    await ctx.message.channel.send(embed=embeds.error_embed(m, ctx))
    logging.error(error_message)


bot.add_cog(TimerManager(bot))
bot.run(config['token'])