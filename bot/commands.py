import lib.database as db
from lib.common import parse_config, get_message_link
from bot.util import is_dm
import lib.time_handle as th

import time
import pytz
import asyncio
from nextcord.ext import commands
from math import floor


config = parse_config('discord')

class TimerManager:

    def __init__(self):
        self.bot = bot

    @commands.command(aliases=['timezone', 'tz'])
    async def set_timezone(self, ctx, *timezone):
        user = db.get_user(ctx.author.id)
        if user is None:
            user = db.User(ctx.author.id, 'Etc/GMT0')
            user.create()

        if len(timezone) == 0:
            m = '''
            Your current timezone is ``{0}``
            Run ``{1} timezone [timezone|utc offset]`` to set it to a different value. \n.
            Here is a list of all available timezones: {2} \n
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

        m = f'''The timezone ``{0}`` can\'t be found. 
        Here is a list of all available timezones: {1}'''.format(timezone, config['timezone_list'])
        await ctx.send(m)
        return

    @commands.command(aliases=['when'])
    async def when_timestamp(self, ctx, *timestamp):
        user = db.get_user(ctx.author.id)
        if user is None:
            user = db.User(ctx.author.id, 'Etc/GMT0')
            user.create()

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
    async def remind_me(self, ctx, timestamp):
        pass

    @commands.command(aliases=['list'])
    async def reminder_list():
        pass


async def timer_list(client, message, msg, db_connection):
    user = db.get_user(db_connection, message.author.id)
    if user is None:
        m = 'You don\'t have any timers set yet.'
        await message.channel.send(m)

    timers = db.get_timers(db_connection, message.author.id)
    # timers = id | label | timestamp_created | timestamp_triggered | author_id | receiver_id | guild | channel | message
    # rows = label | timestamp_created | timestamp_triggered | author_id | receiver_id | link
    row = '| {0} | {1} | {2} | {3} | {4} |\n\n'
    

    def make_length(string, l):
        if len(string) >= l:
            return string[:l]

        white = ''.join([' ' for _ in range(floor((l - len(string))/2))])
        extrawhitespace = ' ' if divmod(l - len(string), 2)[1] == 1 else ''
        return white + extrawhitespace + string + white

    row_data = []
    for t in timers:
        label = str(t[1])
        timestamp_created = time.ctime(t[2])
        timestamp_triggered = time.ctime(t[3])
        author = str(client.get_user(t[4]))
        receiver = str(client.get_user(t[5]))
        #link = make_length(get_message_link(t[6], t[7], t[8], t[4]), 70)
        row_data.append((label, timestamp_created, timestamp_triggered, author, receiver))

    max_lens = []
    max_lens.append(max([len(i[0]) for i in row_data]))
    max_lens.append(max([len(i[1]) for i in row_data]))
    max_lens.append(max([len(i[2]) for i in row_data]))
    max_lens.append(max([len(i[3]) for i in row_data]))
    max_lens.append(max([len(i[4]) for i in row_data]))

    s = sum(max_lens) + len(max_lens) * 3

    rows = []
    # rows.append(''.join(['-' for _ in range(s)]) + '\n')

    for t in row_data:
        label = make_length(t[0], max_lens[0])
        timestamp_created = make_length(t[1], max_lens[1])
        timestamp_triggered = make_length(t[2], max_lens[2])
        author = make_length(t[3], max_lens[3])
        receiver = make_length(t[4], max_lens[4])
        r = row.format(label, timestamp_created, timestamp_triggered, author, receiver)
        rows.append(r)

    # rows.append(''.join(['-' for _ in range(s)]) + '\n')

    messages = []
    while len(rows) > 0:
        partial_rows = []
        while True:
            partial_rows.append(rows[0])
            del rows[0]
            if len(rows) < 1:
                break
            if len(''.join(partial_rows)) + len(rows[0]) > 1900:
                break
        messages.append(''.join(partial_rows))

    if len(messages) < 1:
        await message.channel.send('You have not set any commands yet.')
        return

    for partial_message in messages:
        m = '''```\n{}```'''.format(partial_message)
        await message.channel.send(m)
        await asyncio.sleep(3)


async def set_personal_reminder(client, message, msg, db_connection):
    user = db.get_user(db_connection, message.author.id)
    if user is None:
        m = 'Your timezone isn\'t set yet. Run ``{} timezone`` to set it.'.format(config['prefix'])
        db.create_user(db_connection, message.author.id, 'Etc/GMT0')
        await message.channel.send(m)
        return

    if len(msg) < 2:
        await message.channel.send('Please specify a time')
        return

    if len(msg) < 3:
        msg.append('timer')

    try:
        distance = th.timedelta_string_into_seconds(msg[1])
        seconds_since_epoch = time.time() + distance
    except:
        try:
            seconds_since_epoch = th.timepoint_string_to_seconds(msg[1], user[1])
            seconds_since_epoch = th.localize_seconds(seconds_since_epoch, user[1])
            distance = seconds_since_epoch - time.time()
        except Exception as e:
            await message.channel.send('''Error occured: ```{}``` 
                Be sure to use this format: ``{} when``'''.format(e, config['prefix']))
            return

    datetime_object = th.seconds_to_datetime(seconds_since_epoch)
    datetime_object = th.localize_datetime(datetime_object, user[1])
    timedelta_string = th.timedelta_seconds_to_string(distance)
    datetime_string = datetime_object.ctime()

    channel = message.channel

    if is_dm(channel):
        guild = 0
    else:
        guild = message.channel.guild.id

    channel = channel.id

    m = '''Timer **{0}** set for you **{1}** which is in **{2}**'''\
    .format(msg[2], datetime_string, timedelta_string)

    db.create_timer(db_connection, msg[2], time.time(), seconds_since_epoch, \
     message.author.id, receiver_id=message.author.id, guild_id=guild, \
     channel_id=channel, message_id=message.id)

    await message.channel.send(m)



#register_command(set_personal_reminder, name='personal', aliases=['me'])
register_command(set_timezone, name='timezone', aliases=['tz'])
register_command(when, name='when', aliases=[])
register_command(set_personal_reminder, name='me', aliases=['m', 'myself'])
register_command(timer_list, name='list', aliases=['l'])