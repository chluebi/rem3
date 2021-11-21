import lib.database as db
from lib.common import parse_config, get_message_link
from bot.util import is_dm
import lib.time_handle as th

import time
import pytz
import asyncio
from nextcord.ext import commands, tasks
from math import floor


config = parse_config('discord')

class TimerManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['timezone', 'tz'])
    async def set_timezone(self, ctx, *timezone):
        timezone = ' '.join(timezone)
        user = db.User.get(ctx.author.id)
        if user is None:
            user = db.User(ctx.author.id, 'Etc/GMT0')
            user.create()

        if len(timezone) == 0:
            m = '''Your current timezone is ``{0}``
Run ``{1} timezone [timezone|utc offset]`` to set it to a different value.
Here is a list of all available timezones: {2}
            '''.format(user.timezone, config['prefix'], config['timezone_list'])
            await ctx.send(m)
            return
        
        if timezone == user.timezone:
            m = f'Your timezone is already ``{timezone}``.'
            await ctx.send(m)
            return

        if timezone.startswith('+') or timezone.startswith('-') or timezone.startswith('0'):
            gmt = 'Etc/GMT'
            if int(timezone) <= 12 and int(timezone) >= -14:
                if int(timezone) >= 0:
                    timezone = gmt + '+' + str(-int(timezone))
                else:
                    timezone = gmt + '-' + str(-int(timezone))
                user.change_timezone(timezone)
                m = f'Your timezone has been set to ``{timezone}``. \n'
                await ctx.send(m)
                return
            else:
                await ctx.send('``{timezone}`` is not a valid utc offset')

        if timezone in pytz.all_timezones:
            user.change_timezone(timezone)
            m = f'Your timezone has been set to ``{timezone}``. \n'
            await ctx.send(m)
            return

        m = '''The timezone ``{0}`` can\'t be found. 
Here is a list of all available timezones: {1}'''.format(timezone, config['timezone_list'])
        await ctx.send(m)
        return

    @commands.command(aliases=['when'])
    async def when_timestamp(self, ctx, timestamp):
        user = db.User.get(ctx.author.id)
        if user is None:
            user = db.User(ctx.author.id, 'Etc/GMT0')
            user.create()
            m = 'Your timezone isn\'t set yet. Run ``{} timezone`` to set it.'.format(config['prefix'])
            await ctx.send(m)
            return

        try:
            distance = th.timedelta_string_into_seconds(timestamp)
            seconds_since_epoch = time.time() + distance
        except:
            try:
                seconds_since_epoch = th.timepoint_string_to_seconds(timestamp, user.timezone)
                seconds_since_epoch = th.localize_seconds(seconds_since_epoch, user.timezone)
                distance = seconds_since_epoch - time.time()
            except Exception as e:
                await ctx.send(f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``''')
                return

        datetime_object = th.seconds_to_datetime(seconds_since_epoch)
        datetime_object = th.localize_datetime(datetime_object, user.timezone)
        timedelta_string = th.timedelta_seconds_to_string(distance)
        datetime_string = datetime_object.ctime()
        m = '''This timestamp is in ``{0}`` which is the ``{1}``'''\
        .format(timedelta_string, datetime_string)

        await ctx.send(m)

        

    @commands.command(aliases=['me', 'm'])
    async def remind_me(self, ctx, timestamp, *label):
        label = ' '.join(label)
        user = db.User.get(ctx.author.id)
        if user is None:
            user = db.User(ctx.author.id, 'Etc/GMT0')
            user.create()
            m = 'Your timezone isn\'t set yet. Run ``{} timezone`` to set it.'.format(config['prefix'])
            await ctx.send(m)
            return

        if len(label) == 0:
            label = 'timer'

        try:
            distance = th.timedelta_string_into_seconds(timestamp)
            seconds_since_epoch = time.time() + distance
        except:
            try:
                seconds_since_epoch = th.timepoint_string_to_seconds(timestamp, user.timezone)
                seconds_since_epoch = th.localize_seconds(seconds_since_epoch, user.timezone)
                distance = seconds_since_epoch - time.time()
            except Exception as e:
                await ctx.send(f'''Error ``{e}`` occurred, could not parse timestamp ``{timestamp}``''')
                return

        datetime_object = th.seconds_to_datetime(seconds_since_epoch)
        datetime_object = th.localize_datetime(datetime_object, user.timezone)
        timedelta_string = th.timedelta_seconds_to_string(distance)
        datetime_string = datetime_object.ctime()

        channel = ctx.channel

        if is_dm(channel):
            guild = 0
        else:
            guild = ctx.channel.guild

        m = '''Timer **{0}** set for you **{1}** which is in **{2}**'''\
        .format(label, datetime_string, timedelta_string)

        timer = db.Timer(0, label, time.time(), seconds_since_epoch, ctx.author.id, ctx.author.id, guild.id, channel.id, ctx.message.id)
        timer.create()
        await ctx.send(m)

    @commands.command(aliases=['list'])
    async def reminder_list(self, ctx):
        user = db.User.get(ctx.author.id)
        if user is None:
            user = db.User(ctx.author.id, 'Etc/GMT0')
            user.create()
            m = 'You have not set any timers yet.'
            await ctx.send(m)
            return

        timers = user.get_timers()
        visual_timers = []

        for t in timers:
            visual_timers.append(
                f'''[{t.id}] 
```{t.label}```
Set at *{time.ctime(t.timestamp_created)}* by {str(self.bot.get(t.author_id))} with message {get_message_link(t.guild, t.channel, t.message, t.receiver_id)}
Will trigger at *{time.ctime(t.timestamp_triggered)}*
                '''
            )

        messages = []
        for t in visual_timers:
            if len(messages[-1]) + len(t):
                messages.append(t)
            else:
                messages[-1] += '\n' + t

        for m in messages:
            await ctx.send(m)
            await asyncio.sleep(3)

    @tasks.loop(seconds=config['interval'])
    async def trigger_timers(self):
        old_time = time.time()
        timers = db.Timer.get_all_later_then(old_time + config['interval'])

        for timer in timers:
            delay = timer.timestamp_triggered - time.time()
            self.bot.loop.create_task(self.trigger_timer(delay, timer))
            timers.remove(timer)

    async def trigger_timer(self, delay, timer):
        await asyncio.sleep(delay)
        if timer.timestamp_triggered > time.time():
            return False, 0

        if timer.timestamp_triggered < time.time() - 2*config['interval']:
            timer.delete()
            return True, id

        receiver = self.bot.get(timer.receiver_id)
        created_message_link = get_message_link(timer.guild, timer.channel, timer.message, timer.receiver_id)

        created_time_string = th.seconds_to_datetime(timer.timestamp_created).ctime()
        triggered_time_string = th.seconds_to_datetime(timer.timestamp_created).ctime()
        error_margin = str(int((time.time() - timer.timestamp_triggered)*1000))
        m = f'''⏰ Timer: ``{timer.label}``
This timer was set on ``{created_time_string}``.
This timer should've triggered on ``{triggered_time_string}``. (Error Margin: {error_margin} ms)
Here is the message where it has been set: {created_message_link}'''

        timer.delete()
        await receiver.send(m)
        return True, id