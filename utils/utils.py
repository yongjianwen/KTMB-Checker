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
    now = malaysia_now_datetime()
    # if interval <= 60:
    #     # e.g. interval = 30
    #     # t= 5 => (60 -  5) % 30 = 55 % 30 = 25 seconds
    #     # t=33 => (60 - 33) % 30 = 27 % 30 = 27 seconds
    #     seconds_until_30_or_60 = (60 - now.second) % interval
    #     ans = now + timedelta(seconds=seconds_until_30_or_60)
    #     ans = ans.replace(microsecond=0)
    # else:
    #     # e.g. interval = 300 (5 minutes)
    #     # m= 3 => (60 -  3) % 5 = 2 minutes
    #     # m=33 => (60 - 33) % 5 = 2 minutes
    #     seconds_until = ((60 - now.minute - 1) % (interval // 60)) * 60
    #     if interval % 60 != 0:
    #         seconds_until = seconds_until + (60 - now.second) % (interval % 60)
    #     ans = now + timedelta(seconds=seconds_until)
    #     ans = ans.replace(microsecond=0)

    if interval <= 60:  # For intervals ≤ 1 minute
        # Calculate next interval in current minute
        next_second = ((now.second // interval) + 1) * interval

        if next_second >= 60:
            # Roll over to next minute
            ans = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        else:
            ans = now.replace(second=next_second, microsecond=0)
    else:
        # For intervals > 1 minute
        interval_minutes = interval // 60
        current_minute = now.minute
        next_minute = ((current_minute // interval_minutes) + 1) * interval_minutes

        if next_minute >= 60:
            # Roll over to next hour
            ans = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            ans = now.replace(minute=next_minute, second=0, microsecond=0)

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
