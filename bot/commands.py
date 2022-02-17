from pydoc import describe
from nextcord.gateway import DiscordClientWebSocketResponse
import lib.database as db
from lib.common import parse_config, get_message_link, get_channel_link
from bot.util import is_dm
import lib.time_handle as th
from bot import embeds, checks

import time
import calendar
import pytz
import asyncio
import re
from nextcord.ext import commands, tasks
from math import floor


config = parse_config('discord')

class TimerManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.trigger_timers.start()

    @commands.command(aliases=['timezone', 'tz'], description="Sets the user's timezone")
    @commands.check(checks.create_user)
    async def set_timezone(self, ctx, timezone=None):
        '''
        rem (timezone|tz) [timezone|utc offset|current time]
        Sets the user's timezone
        
        arguments:
        timezone: a timezone string
        utc offset: 0 or a number with + or - as prefix
        '''

        user = db.User.get(ctx.author.id)


        # default embed for no argument
        if timezone is None:
            user_now = th.seconds_to_datetime(time.time())
            user_now = th.localize_datetime(user_now, user.timezone)
            user_now = user_now.strftime('%H:%M')

            m = '''Your current timezone is ``{0}``

If this is the correct timezone the following two times should be identical:
 ``{4}`` and <t:{3}:t>

If this is not the case run "{1} timezone <t:{3}:t>" to set it to your current timezone.
Alternatively you can also type in your UTC offset or if needed your specific timezone.
            '''.format(user.timezone, config['prefix'], config['timezone_list'], int(time.time()), user_now)
            await ctx.send(embed=embeds.standard_embed('Timezone', m, ctx=ctx))
            return

        # UTC offset
        if re.match('(?:(?:\+|\-)\d{1,2})$|0$', timezone):
            gmt = 'Etc/GMT'
            if int(timezone) <= 12 and int(timezone) >= -14:
                if int(timezone) >= 0:
                    timezone = gmt + '+' + str(int(timezone))
                else:
                    timezone = gmt + '-' + str(-int(timezone))

                user.change_timezone(timezone)
                m = f'Your timezone has been set to ``{timezone}``. \n'
                await ctx.send(embed=embeds.success_embed('Timezone updated successfully', m, ctx=ctx))
                return
            else:
                await ctx.send(embed=embeds.error_embed(f'``{timezone}`` is not a valid utc offset', ctx))
                return

        # Absolute time given
        if re.match('(\d\d:[0-6]\d)$', timezone):
            s = re.findall('(\d\d:[0-6]\d)', timezone)[0]

            c = time.gmtime(th.delocalize_seconds(time.time(), 'Etc/GMT0'))
            target_time = time.strptime(f'{c.tm_year}.{c.tm_mon}.{c.tm_mday} {timezone}', '%Y.%m.%d %H:%M')
            seconds = calendar.timegm(target_time)

            # filter all timezones
            possible_timezones = []
            normal_seconds = time.time()
            for tz in pytz.all_timezones:
                localize_seconds = th.delocalize_seconds(normal_seconds, tz)
                if (abs(localize_seconds-seconds) < 300):
                    possible_timezones.append(tz)

            if len(possible_timezones) < 1:
                await ctx.send(embed=embeds.error_embed(f'No timezone where it is currently ``{timezone}`` has been found.', ctx))
                return

            # search for gmt offsets
            possible_gmt_offsets = []
            for tz in possible_timezones:
                if tz.startswith('Etc/'):
                    possible_gmt_offsets.append(tz)

            # if no gmt is found, then give the user a list
            # this is mostly for funky timezones like Nepal with a 15 minute offset
            if len(possible_gmt_offsets) < 1:
                await ctx.send('The following timezones have been found to have this current time: ```{0}``` Please choose one and run the following ``rem tz <timezone>``.'.format('\n'.join(possible_timezones)))
                return
            else:
                tz = possible_gmt_offsets[0]
                user.change_timezone(tz)
                m = 'Your timezone has been set to ``{0}`` '.format(tz)
                await ctx.send(embed=embeds.success_embed('Timezone updated successfully', m, ctx=ctx))
                return

        if timezone in pytz.all_timezones:
            user.change_timezone(timezone)
            m = 'Your timezone has been set to ``{0}`` '.format(timezone)
            await ctx.send(embed=embeds.success_embed('Timezone updated successfully', m, ctx=ctx))
            return

        m = f'''The given argument {timezone} is not valid. Be sure to either pass a time, a valid UTC offset or a valid timezone.'''
        await ctx.send(embed=embeds.error_embed(m, ctx))
        return

    @commands.command(description='Allows another user to set timers for you.')
    @commands.check(checks.create_user)
    async def allow(self, ctx, sender: commands.UserConverter):

        user_db = db.User.get(ctx.author.id)
        sender_db = db.User.get(sender.id)

        if sender_db is None or self.bot.get_user(sender_db.id) is None:
            m = f'''Other user not found.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        if db.Allow.get(sender_db.id, user_db.id) is not None:
            m = f'''This user is already allowed to set timers for you.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))

        allow = db.Allow.create(sender_db.id, user_db.id)
        allow.insert()

        m = f'''Successfully allowed {sender.mention} to set timers for you.'''
        await ctx.send(embed=embeds.success_embed('Successfully Allowed', m, ctx=ctx))


    @commands.command(aliases=['unallow'], description='Disallows another user to set timers for you.')
    @commands.check(checks.create_user)
    async def disallow(self, ctx, sender: commands.UserConverter):

        user_db = db.User.get(ctx.author.id)
        sender_db = db.User.get(sender.id)

        if sender_db is None or self.bot.get_user(sender_db.id) is None:
            m = f'''Other user not found.'''
            
            if sender_db is not None:
                allow = db.Allow.get(sender_db.id, user_db.id)
                if allow is not None:
                    m += '\nDisallowed anyway.'
                    allow.delete()

            await ctx.send(embed=embeds.error_embed(m, ctx))

            return

        allow = db.Allow.get(sender_db.id, user_db.id)
        if allow is None:
            m = f'''This user is already disallowed to set timers for you.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))

        allow.delete()

        m = f'''Successfully disallowed {sender.mention} to set timers for you.'''
        await ctx.send(embed=embeds.success_embed('Successfully Disallowed', m, ctx=ctx))


    @commands.command(aliases=['when', 'timestamp'], description='Gives the absolute date and relative distance to a timestamp')
    @commands.check(checks.create_user)
    async def when_timestamp(self, ctx, timestamp):
        '''[relative or absolute timestamp]'''

        user = db.User.get(ctx.author.id)

        try:
            timestamp_seconds = th.parse_time_string(timestamp, user)
        except Exception as e:
            m = f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        m = '''This timestamp is in <t:{0}:R>'''.format(int(timestamp_seconds))

        await ctx.send(embed=embeds.standard_embed('Timestamp', m, ctx=ctx))

        

    @commands.command(aliases=['me', 'm'], description='Sets a personal timer for the person calling the command')
    @commands.check(checks.create_user)
    async def remind_me(self, ctx, timestamp, *label):
        '''(relative or absolute timestamp) (*message attached to the timer)'''
        label = ' '.join(label)
        user = db.User.get(ctx.author.id)

        if len(label) == 0:
            label = 'Unnamed Timer'

        if len(label) > 1000:
            m = f'''Timer labels are limited to at maximum 1000 characters.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        split_timestamp = timestamp.split('-')
        if (len(split_timestamp) == 1):
            timestamp = split_timestamp[0]
            repeat_timestamp = 0
        elif (len(split_timestamp) == 2):
            timestamp = split_timestamp[0]
            repeat_timestamp = split_timestamp[1]
        else:
            m = f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        try:
            timestamp_seconds = th.parse_time_string(timestamp, user)
        except Exception as e:
            m = f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        if (repeat_timestamp == 0):
            repeat_timestamp_seconds = 0
        else:
            try:
                repeat_timestamp_seconds = th.timedelta_string_into_seconds(repeat_timestamp)
                if (repeat_timestamp_seconds < config['min_repeat']):
                    m = '''The minimum duration of repeating a timer is ``{0}``'''.format(th.timedelta_seconds_to_string(config['min_repeat']))
                    await ctx.send(embed=embeds.error_embed(m, ctx))
                    return
            except Exception as e:
                m = f'''Error ``{e}`` occurred, could not parse repeat timestamp ``{repeat_timestamp}``'''
                await ctx.send(embed=embeds.error_embed(m, ctx))
                return

        if is_dm(ctx.channel):
            guild_id = 0
        else:
            guild_id = ctx.channel.guild.id

        timer = db.Timer.create_personal_timer(label, time.time(), timestamp_seconds, ctx.author.id, ctx.author.id, guild_id, ctx.channel.id, ctx.message.id, repeat=repeat_timestamp_seconds)

        m = '''[ID: {2}]
        {0}
        
        set for you to trigger in <t:{1}:R>'''.format(label, int(timestamp_seconds), timer.id)
        if (repeat_timestamp_seconds > 0):
            m += '\nThe timer will repeat every {0}'.format(th.timedelta_seconds_to_string(repeat_timestamp_seconds))

        timer.insert()
        await ctx.send(embed=embeds.success_embed('Timer Set', m, ctx=ctx))


    @commands.command(aliases=['them'], description='Sets a personal timer for another user')
    @commands.check(checks.create_user)
    async def remind_them(self, ctx, receiver : commands.UserConverter, timestamp, *label):
        '''(relative or absolute timestamp) (*message attached to the timer)'''
        label = ' '.join(label)

        author_db = db.User.get(ctx.author.id)
        receiver_db = db.User.get(receiver.id)

        if receiver_db is None or self.bot.get_user(receiver_db.id) is None:
            m = f'''Other user not found.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        if db.Allow.get(author_db.id, receiver_db.id) is None and author_db.id != receiver_db.id:
            m = '''You are not allowed to set timers for this user.
They can allow you to send timers by calling ``{0} allow @you``'''.format(config['prefix'])
            await ctx.send(embed=embeds.error_embed(m, ctx, title='Not Authorized'))
            return

        if len(label) == 0:
            label = 'Unnamed Timer'

        if len(label) > 1000:
            m = f'''Timer labels are limited to at maximum 1000 characters.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        split_timestamp = timestamp.split('-')
        if (len(split_timestamp) == 1):
            timestamp = split_timestamp[0]
            repeat_timestamp = 0
        elif (len(split_timestamp) == 2):
            timestamp = split_timestamp[0]
            repeat_timestamp = split_timestamp[1]
        else:
            m = f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        try:
            try:
                distance = th.timedelta_string_into_seconds(timestamp)
                timestamp_seconds = time.time() + distance
                absolute_timestamp = False
            except Exception as e:
                # Also already makes sure the absolute timestamp given is valid
                seconds_since_epoch = th.timepoint_string_to_seconds(timestamp, author_db.timezone)
                timestamp_seconds = th.localize_seconds(seconds_since_epoch, author_db.timezone)
                absolute_timestamp = True
        except Exception as e:
            m = f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        if absolute_timestamp and pytz.timezone(author_db.timezone).utcoffset.total_seconds() != pytz.timezone(receiver_db.timezone).utcoffset.total_seconds():
            def check(message):
                return message.channel.id == ctx.channel.id and message.author.id == ctx.author.id and message.content in ['0', '1']
            
            m = '''You have given an absolute timestamp for a timer for a user with a different timezone than yours, please specify relative to which timezone you want to set this timer:
Write ``0`` to set the timer relative to your timezone
Write ``1`` to set the timer relative to the receiver's timezone'''
            timezone_specification_message = await ctx.send(embed=embeds.standard_embed('Action Required', m))
            
            try:
                reply_message = await self.bot.wait_for('message', timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await timezone_specification_message.delete()
                return
            else:
                if reply_message.content == '1':
                    seconds_since_epoch = th.timepoint_string_to_seconds(timestamp, receiver_db.timezone)
                    timestamp_seconds = th.localize_seconds(seconds_since_epoch, receiver_db.timezone)
                else:
                    seconds_since_epoch = th.timepoint_string_to_seconds(timestamp, author_db.timezone)
                    timestamp_seconds = th.localize_seconds(seconds_since_epoch, author_db.timezone)

        if (repeat_timestamp == 0):
            repeat_timestamp_seconds = 0
        else:
            try:
                repeat_timestamp_seconds = th.timedelta_string_into_seconds(repeat_timestamp)
                if (repeat_timestamp_seconds < config['min_repeat']):
                    m = '''The minimum duration of repeating a timer is ``{0}``'''.format(th.timedelta_seconds_to_string(config['min_repeat']))
                    await ctx.send(embed=embeds.error_embed(m, ctx))
                    return
            except Exception as e:
                m = f'''Error ``{e}`` occurred, could not parse repeat timestamp ``{repeat_timestamp}``'''
                await ctx.send(embed=embeds.error_embed(m, ctx))
                return

        if is_dm(ctx.channel):
            guild_id = 0
        else:
            guild_id = ctx.channel.guild.id

        timer = db.Timer.create_personal_timer(label, time.time(), timestamp_seconds, ctx.author.id, receiver_db.id, guild_id, ctx.channel.id, ctx.message.id, repeat=repeat_timestamp_seconds)

        m = '''[ID: {2}]
        {0}
        
        set for {3} to trigger in <t:{1}:R>'''.format(label, int(timestamp_seconds), timer.id, receiver.mention)
        if (repeat_timestamp_seconds > 0):
            m += '\nThe timer will repeat every {0}'.format(th.timedelta_seconds_to_string(repeat_timestamp_seconds))

        timer.insert()
        await ctx.send(embed=embeds.success_embed('Timer Set', m, ctx=ctx))


    @commands.command(description='Deletes a timer controlled by the user')
    @commands.check(checks.create_user)
    async def delete(self, ctx, id: int):
        '''Timers that can be deleted are either:
- timers set by the user
- timers set for the user
- timers set in a guild that the user has admin rights in
'''
        user = db.User.get(ctx.author.id)

        timer = db.Timer.get_by_author(id, user.id)
        if timer is None:
            timer = db.Timer.get_by_receiver(id, user.id)

        if timer is None:
            title = 'Timer not Found'
            m = f'Timer of id ``{id}`` not found.'
            await ctx.send(embed=embeds.error_embed(m, ctx, title=title))
            return

        timer.delete()
        title = 'Timer Deleted'
        m = f'Timer of id ``{id}`` deleted.'
        await ctx.send(embed=embeds.success_embed(title, m, ctx=ctx))


    @commands.command(aliases=['list'], description='Gives the entire list of reminders for a user.')
    @commands.check(checks.create_user)
    @commands.check(checks.is_dm)
    async def reminder_list(self, ctx):
        '''[DM-only]'''

        user = db.User.get(ctx.author.id)

        receiver_timers = user.get_timers_by_receiver()
        author_timers = user.get_timers_by_author()
        author_timers = [timer for timer in author_timers if timer.author_id != timer.receiver_id]

        if len(receiver_timers) == 0 and len(author_timers) == 0:
            m = 'There are no timers yet connected to you.'
            await ctx.send(embed=embeds.error_embed(m, ctx, title='No Timers'))
            return

        embed_list = []

        if len(receiver_timers) > 0:
            visual_timers = []
            for timer in receiver_timers:
                text = f'[ID: {timer.id}] '
                if timer.author_id != timer.receiver_id:
                    other_user = self.bot.get_user(timer.author_id)
                    if other_user is None:
                        other_user = '``User not found``'
                    text += f'by {other_user} '
                text += f'**{timer.label[:20]}** <t:{int(timer.triggered_timestamp)}:R>'
                if (timer.repeat_seconds != 0):
                    text += f' repeating every {th.timedelta_seconds_to_string(timer.repeat_seconds)}'

                visual_timers.append(text)

            m = f'''A list of all timers which will eventually trigger for you.
            Total Timers: {len(receiver_timers)}
            '''
            embed_list += embeds.list_embed('Timers set for you', m, visual_timers)

        if len(author_timers) > 0:
            visual_timers = []
            for timer in author_timers:
                text = f'[ID: {timer.id}] '
                if timer.receiver_guild_id == 0:
                    other_user = self.bot.get_user(timer.receiver_id)
                    if other_user is None:
                        other_user = '``User not found``'
                    text += f'for {other_user} '
                else:
                    channel_link = get_channel_link(timer.receiver_guild_id, timer.receiver_channel_id)
                    text += f'in [here]({channel_link})'

                text += f'**{timer.label[:20]}** <t:{int(timer.triggered_timestamp)}:R>'
                if (timer.repeat_seconds != 0):
                    text += f' repeating every {th.timedelta_seconds_to_string(timer.repeat_seconds)}'
                
                visual_timers.append(text)

            m = f'''A list of all timers set by you.
            Total Timers: {len(author_timers)}
            '''
            embed_list += embeds.list_embed('Timers created by you', m, visual_timers)

        for e in embed_list:
            await ctx.send(embed=e)
            await asyncio.sleep(3)

    @tasks.loop(seconds=config['interval'])
    async def trigger_timers(self):
        old_time = time.time()
        timers = db.Timer.get_all_later_then(old_time + config['interval'])

        for timer in timers:
            delay = timer.triggered_timestamp - time.time()
            self.bot.loop.create_task(self.trigger_timer(delay, timer))
            timers.remove(timer)

    async def trigger_timer(self, delay, timer: db.Timer):
        await asyncio.sleep(delay)
        if timer.triggered_timestamp > time.time():
            return False, 0

        if timer.triggered_timestamp < time.time() - 2*config['interval']:
            timer.delete()
            return True, id

        receiver = self.bot.get_user(timer.receiver_id)
        created_message_link = get_message_link(timer.author_guild_id, timer.author_channel_id, timer.author_message_id, timer.author_id)

        error_margin = str(int((time.time() - timer.triggered_timestamp)*1000))
        m = f'''{timer.label}

        This timer was set <t:{int(timer.created_timestamp)}:R>.
This timer should've triggered <t:{int(timer.triggered_timestamp)}:R>. (Error Margin: {error_margin} ms)'''

        if (timer.author_id == timer.receiver_id):
            m += f'\nThis timer was set in [this message]({created_message_link}).'

        if (timer.receiver_id != 0 and timer.author_guild_id == timer.receiver_guild_id and timer.author_channel_id == timer.receiver_channel_id):
            m += f'\nThis timer was set in [this message]({created_message_link}).'

        if (timer.repeat_seconds > 0):
            m += '\nThis timer repeats every {0}'.format(th.timedelta_seconds_to_string(timer.repeat_seconds))

        timer.delete()
        if (timer.repeat_seconds > 0):
            timer.triggered_timestamp += timer.repeat_seconds
            timer.insert()

        embed = embeds.standard_embed('⏰ Timer Triggered ⏰', m)

        author = self.bot.get_user(timer.author_id)
        if author is not None:
            embed.set_footer(text=f'Timer created by {str(author)}', icon_url=author.avatar.url)
        await receiver.send(embed=embed)
        return True, id