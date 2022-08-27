import discord.ext

import lib.database as db
from lib.common import parse_config
from bot.util import is_dm as channel_is_dm
from bot import embeds, util

config = parse_config('discord')

async def create_user(ctx):
    user = db.User.get(ctx.author.id)
    if user is None:
        user = db.User(ctx.author.id, 'Etc/GMT0')
        user.insert()
        m = 'You have just been added to the database of users.\nYour timezone isn\'t set yet. Run ``{} timezone`` to set it.'.format(config['prefix'])
        embed = embeds.success_embed('User created', m, ctx)
        await util.success_message(embed, ctx)
    return True

async def create_guild(ctx):
    if ctx.guild is None:
        return True
    guild = db.Guild.get(ctx.guild.id)
    if guild is None:
        guild = db.Guild(ctx.guild.id, False, False, False)
        guild.insert()
        m = 'This guild has just been added to the database of guilds. By Default most actions including the ability to set timers inside of the guild are turned off. Admins can run ``{} guild`` to configure the settings.'.format(config['prefix'])
        embed = embeds.success_embed('Guild created', m, ctx)
        await util.success_message(embed, ctx)
    return True

async def is_dm(ctx):
    if not channel_is_dm(ctx.channel):
        m = 'This command is only available in DMs.'
        embed = embeds.error_embed('Check Failure', m, ctx)
        await util.error_message(embed, ctx)
        return False
    return True

async def is_not_dm(ctx):
    if channel_is_dm(ctx.channel):
        m = 'This command cannot be used in DMs.'
        embed = embeds.error_embed('Check Failure', m, ctx)
        await util.error_message(embed, ctx)
        return False
    return True