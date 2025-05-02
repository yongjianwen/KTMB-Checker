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
