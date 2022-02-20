import logging
import traceback

from nextcord.ext import commands
import nextcord

from lib.common import parse_config
from bot.commands import TimerManager
from bot import util, embeds

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

bot.remove_command('help')

@bot.command(name='help')
async def help(ctx):
    await ctx.send(embed=embeds.standard_embed('Help', 'Help can found be on the [official website.](https://chluebi.github.io/rem3/)', ctx=ctx))

@bot.event
async def on_command_error(ctx, error):
    error_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    
    if (isinstance(error, nextcord.ext.commands.CommandNotFound)):
        await ctx.message.add_reaction('❌')
        return

    if (isinstance(error, nextcord.ext.commands.CheckFailure)):
        await ctx.message.add_reaction('❌')
        return

    if (isinstance(error, nextcord.ext.commands.MissingRequiredArgument)):
        await ctx.message.add_reaction('❌')
        return

    if (isinstance(error, nextcord.ext.commands.errors.UserNotFound)):
        await ctx.message.add_reaction('❌')
        return

    m = f'''```{error}```

Probably contact Lu'''
    await util.error_message(embeds.error_embed('Internal Error', m, ctx), ctx, delete=False)
    logging.error(error_message)


bot.add_cog(TimerManager(bot))
bot.run(config['token'])