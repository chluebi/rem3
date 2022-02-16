from nextcord.gateway import DiscordClientWebSocketResponse
import lib.database as db
from lib.common import parse_config, get_message_link
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
                await ctx.send(embed=embeds.success_embed('Timezone updated successfully', m, ctx))
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
                await ctx.send(embed=embeds.success_embed('Timezone updated successfully', m, ctx))
                return

        if timezone in pytz.all_timezones:
            user.change_timezone(timezone)
            m = 'Your timezone has been set to ``{0}`` '.format(timezone)
            await ctx.send(embed=embeds.success_embed('Timezone updated successfully', m, ctx))
            return

        m = f'''The given argument {timezone} is not valid. Be sure to either pass a time, a valid UTC offset or a valid timezone.'''
        await ctx.send(embed=embeds.error_embed(m, ctx))
        return

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

        

    @commands.command(aliases=['me', 'm'], description='Sets a personal reminder for the person calling the command')
    @commands.check(checks.create_user)
    async def remind_me(self, ctx, timestamp, *label):
        '''[relative or absolute timestamp] [*message attached to the reminder]'''
        label = ' '.join(label)
        user = db.User.get(ctx.author.id)

        if len(label) == 0:
            label = 'Unnamed Timer'

        if len(label) > 1000:
            m = f'''Timer labels are limited to at maximum 1000 characters.'''
            await ctx.send(embed=embeds.error_embed(m, ctx))
            return

        split_timestamp = timestamp.split('-')
        print(split_timestamp)
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

        m = '''{0}
        
        set for you to trigger in <t:{1}:R>'''.format(label, int(timestamp_seconds))

        if (repeat_timestamp_seconds > 0):
            m += '\nThe timer will repeat every {0}'.format(th.timedelta_seconds_to_string(repeat_timestamp_seconds))

        timer = db.Timer.create_personal_timer(label, time.time(), timestamp_seconds, ctx.author.id, ctx.author.id, guild_id, ctx.channel.id, ctx.message.id, repeat=repeat_timestamp_seconds)
        timer.insert()
        await ctx.send(embed=embeds.standard_embed('Timer Set', m, ctx=ctx))

    @commands.command(aliases=['list'], description='Gives the entire list of reminders for a user.')
    @commands.check(checks.create_user)
    @commands.check(checks.is_dm)
    async def reminder_list(self, ctx):
        '''[DM-only]'''

        user = db.User.get(ctx.author.id)

        timers = user.get_timers()
        visual_timers = []

        if len(timers) == 0:
            m = 'You have not set any timers yet.'
            await ctx.send(m)
            return

        for timer in timers:
            if (timer.repeat_seconds != 0):
                visual_timers.append(
                    f'[ID: {timer.id}] **{timer.label[:20]}** in <t:{int(timer.triggered_timestamp)}:R> repeating every {th.timedelta_seconds_to_string(timer.repeat_seconds)}'
                )
            else:
                visual_timers.append(
                    f'[ID: {timer.id}] **{timer.label[:20]}** in <t:{int(timer.triggered_timestamp)}:R>'
                )

        embed_list = embeds.list_embed('All timers', 'A list of all timers which eventually will trigger for you.', visual_timers)

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