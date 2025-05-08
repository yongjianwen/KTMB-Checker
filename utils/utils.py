from datetime import datetime, timedelta

import pytz

MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


def malaysia_time_to_utc(user_time):
    """Convert naive Malaysia time to UTC"""
    # First localize to Malaysia time, then convert to UTC
    localized = MALAYSIA_TZ.localize(user_time)
    return localized.astimezone(pytz.utc)


def utc_to_malaysia_time(utc_time):
    """Convert UTC time to Malaysia time"""
    return utc_time.astimezone(MALAYSIA_TZ)


def malaysia_now_datetime():
    return datetime.now(MALAYSIA_TZ)


def malaysia_now_time():
    return datetime.now(MALAYSIA_TZ).time()


# def get_next_zero_second():
#     now = malaysia_now_datetime()
#     # Calculate seconds until the next minute
#     seconds_until_next_minute = 60 - now.second
#     next_zero_second = now + timedelta(seconds=seconds_until_next_minute)
#     # Set microseconds to 0 for precision
#     next_zero_second = next_zero_second.replace(microsecond=0)
#     return next_zero_second


def get_next_time_by_interval(interval):
    """
    interval must be < 60
    """
    now = malaysia_now_datetime()
    # e.g. interval = 30
    # t= 5 => (60 -  5) % 30 = 55 % 30 = 25 seconds
    # t=33 => (60 - 33) % 30 = 27 % 30 = 27 seconds
    seconds_until_30_or_60 = (60 - now.second) % interval
    ans = now + timedelta(seconds=seconds_until_30_or_60)
    ans = ans.replace(microsecond=0)
    return ans


def get_weekday(weekday):
    return {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }.get(weekday, '')


def get_number_emoji_from(number):
    emojis = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    ans = ''
    while number:
        temp = number % 10
        ans = emojis[temp] + ans
        number = number // 10
    return ans
