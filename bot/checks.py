import nextcord.ext

import lib.database as db
from lib.common import parse_config
from bot.util import is_dm as channel_is_dm
from bot import embeds

config = parse_config('discord')

async def create_user(ctx):
    user = db.User.get(ctx.author.id)
    if user is None:
        user = db.User(ctx.author.id, 'Etc/GMT0')
        user.insert()
        m = 'You have just been added to the database of users.\nYour timezone isn\'t set yet. Run ``{} timezone`` to set it.'.format(config['prefix'])
        await ctx.send(embed=embeds.standard_embed('User created', m, ctx=ctx))
    return True

async def create_guild(ctx):
    guild = db.Guild.get(ctx.guild.id)
    if guild is None:
        guild = db.Guild(ctx.guild.id, False, False)
        guild.insert()
    return True

async def is_dm(ctx):
    if not channel_is_dm(ctx.channel):
        m = 'This command is only available in DMs.'
        await ctx.send(embed=embeds.error_embed(m, ctx, title='Check Failure'))
        return False
    return True