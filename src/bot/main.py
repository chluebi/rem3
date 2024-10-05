import logging
import traceback
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('.testenv')

from discord.ext import commands
import discord

from src.bot.commands import TimerManager
from src.bot import util, embeds

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='{0} '.format(os.getenv('PREFIX')), intents=intents)

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
    
    if (isinstance(error, discord.ext.commands.CommandNotFound)):
        await ctx.message.add_reaction('❌')
        return

    if (isinstance(error, discord.ext.commands.CheckFailure)):
        await ctx.message.add_reaction('❌')
        return

    if (isinstance(error, discord.ext.commands.MissingRequiredArgument)):
        await ctx.message.add_reaction('❌')
        return

    if (isinstance(error, discord.ext.commands.errors.UserNotFound)):
        await ctx.message.add_reaction('❌')
        return

    m = f'''```{error}```

Probably contact Lu'''
    await util.error_message(embeds.error_embed('Internal Error', m, ctx), ctx, delete=False)
    logging.error(error_message)


asyncio.run(bot.add_cog(TimerManager(bot)))

bot.run(os.getenv('DISCORD_TOKEN'))