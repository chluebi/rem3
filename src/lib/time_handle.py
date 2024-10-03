import time
import datetime
import calendar
import pytz


# This horribly long function takes in a string like "3h 20m"
# and returns the value of it in seconds
#
# It achieves this magic by what experts call
# "a for loop and a bunch of booleans"
def timedelta_string_into_seconds(timestring):
    NUMS = ['0','1','2','3','4','5','6','7','8','9','.']
    time_values = {'s':1,
                   'sec':1,
                   'm':60,
                   'min':60,
                   'h':3600,
                   'd':3600*24,
                   'w':3600*24*7,
                   'mon':3600*24*31,
                   'y':3600*24*365}
    end = []
    num = False
    abc = False
    timestring = timestring.replace(' ','')
    for let in timestring:
        if abc and num:
            raise Exception('This shouldn\'t happen')
        elif num:
            if let not in NUMS:
                end[-1][0] += let
            else:
                end[-1][1] += let
        elif abc:
            if let not in NUMS:
                end[-1][0] += let
            else:
                end.append(['', let])
        else:
            if let not in NUMS:
                num = False
                abc = not num
                continue

            end.append(['',let])

        abc = let not in NUMS
        num = not abc

    endsum = 0
    for form, amount in end:
        try:
            endsum += time_values[form] * float(amount)
        except:
            raise Exception(f'{form} is not a valid timetype')


    return endsum

# Does the opposite of the function above
def timedelta_seconds_to_string(seconds):
    time_values = {'year': 3600 * 24 * 365,
                   'month': 3600 * 24 * 31,
                   'week': 3600 * 24 * 7,
                   'day': 3600 * 24,
                   'hour': 3600,
                   'minute': 60,
                   'second': 1
                   }

    rest = seconds
    end = []
    for key, value in time_values.items():
        if rest >= value:
            amount = int(rest // value)
            rest = rest % value
            if amount == 1:
                end.append(f'{amount} {key}')
            else:
                end.append(f'{amount} {key}s')

    if len(end) > 1:
        endstring = ', '.join(end[:-1])
        endstring += f' and {end[-1]}'
    elif len(end) > 0:
        endstring = end[0]
    else:
        endstring = '0 seconds'

    return endstring


# Tries a lot of different formats to find one that sticks
def strptime_list(timestring, timezone):
    try:
        return time.strptime(timestring, '%Y')
    except:
        pass
    try:
        return time.strptime(timestring, '%Y.%m.%d')
    except:
        pass
    try:
        return time.strptime(timestring, '%d.%m.%Y')
    except:
        pass
    try:
        return time.strptime(timestring, '%Y.%m.%d %H:%M')
    except:
        pass
    try:
        return time.strptime(timestring, '%d.%m.%Y %H:%M')
    except:
        pass
    try:
        return time.strptime(timestring, '%H:%M %d.%m.%Y')
    except:
        pass
    try:
        c = time.gmtime(delocalize_seconds(time.time(), timezone))
        end = time.strptime(f'{c.tm_year}.{c.tm_mon}.{c.tm_mday} {timestring}', '%Y.%m.%d %H:%M')
        # if the specified time has already passed today,
        # we just get the same point in time but the next day
        if calendar.timegm(end) < delocalize_seconds(time.time(), timezone):
            end = time.gmtime(calendar.timegm(end) + 3600*24)
        return end
    except:
        pass
    try:
        c = time.gmtime(delocalize_seconds(time.time(), timezone))
        end = time.strptime(f'{c.tm_year}.{c.tm_mon}.{c.tm_mday} {timestring}', '%Y.%m.%d %H:%M:%S')
        # if the specified time has already passed today,
        # we just get the same point in time but the next day
        if calendar.timegm(end) < delocalize_seconds(time.time(), timezone):
            end = time.gmtime(calendar.timegm(end) + 3600*24)
        return end
    except:
        pass


# calls the function above, but with better verbose output
def timepoint_string_to_seconds(timestring, timezone):
    target_time = strptime_list(timestring, timezone)
    if target_time is None:
        raise Exception('Not a valid format')
    return calendar.timegm(target_time)

def seconds_to_datetime(seconds):
    gmt = datetime.datetime.utcfromtimestamp(seconds)
    return gmt

# puts an amount of seconds from one timezone into POSIX
def delocalize_seconds(seconds, timezone):
    timezone = pytz.timezone(timezone)
    datetime_object = seconds_to_datetime(seconds)
    offset = timezone.utcoffset(datetime_object).total_seconds()
    return seconds + offset


# puts POSIX into timezone
def localize_seconds(seconds, timezone):
    timezone = pytz.timezone(timezone)
    datetime_object = seconds_to_datetime(seconds)
    offset = timezone.utcoffset(datetime_object).total_seconds()
    return seconds - offset


# same as above but for datetime objects
def localize_datetime(datetime_object, timezone):
    timezone = pytz.timezone(timezone)
    return pytz.utc.localize(datetime_object).astimezone(timezone)


def delocalize_datetime(datetime_object, timezone):
    timezone = pytz.timezone(timezone)
    return timezone.localize(datetime_object).astimezone(timezone)



def parse_time_string(timestamp, user):
    try:
        distance = timedelta_string_into_seconds(timestamp)
        seconds_since_epoch = time.time() + distance
    except:
        seconds_since_epoch = timepoint_string_to_seconds(timestamp, user.timezone)
        seconds_since_epoch = localize_seconds(seconds_since_epoch, user.timezone)
        distance = seconds_since_epoch - time.time()

    datetime_object = seconds_to_datetime(seconds_since_epoch)
    datetime_object = localize_datetime(datetime_object, user.timezone)
    timedelta_string = timedelta_seconds_to_string(distance)
    datetime_string = datetime_object.ctime()

    return seconds_since_epoch