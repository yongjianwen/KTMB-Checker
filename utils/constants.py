from enum import Enum

# Regex
UUID_PATTERN = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
DATE_PATTERN = '\\d{4}-\\d{2}-\\d{2}'

# User data keys
COOKIE = 'cookie'
TOKEN = 'token'
EMAIL = 'email'
PASSWORD = 'password'
LAST_MESSAGE = 'last_message'
STATE = 'state'
TO_STRIKETHROUGH = 'to_strikethrough'
TO_HIDE_KEYBOARD = 'to_hide_keyboard'

PROFILES = 'profiles'
SHORTCUTS = 'shortcuts'

TEMP = 'temp'
TRANSACTION = 'transaction'
VOLATILE = 'volatile'
STATIONS_DATA = 'stations_data'
TRACKING_LIST = 'tracking_list'

# Transaction keys
FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME = 'from_state_name', 'from_station_id', 'from_station_name'
TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME = 'to_state_name', 'to_station_id', 'to_station_name'
DATE = 'date'
DEPARTURE_TIME, ARRIVAL_TIME = 'departure_time', 'arrival_time'
PRICE = 'price'

# Volatile keys
SEARCH_DATA = 'search_data'
TRIPS_DATA = 'trips_data'
TRIP_DATA = 'trip_data'
LAYOUT_DATA = 'layout_data'
BOOKING_DATA = 'booking_data'
OVERALL_PRICES = 'overall_prices'
PARTIAL_CONTENT = 'partial_content'

# Tracking item keys
TRACKING_UUID = 'tracking_uuid'
RESERVED_SEAT = 'reserved_seat'
SEATS_LEFT_BY_PRICES = 'seats_left_by_prices'
LAST_REMINDED = 'last_reminded'

# Bottom keyboard
TRACK_NEW_TRAIN = 'Track New Train 🚈'
VIEW_TRACKING = '👀 View Tracking'

# Inline keyboard
ADD_NEW_PROFILE = '+ New Profile'
ADD_NEW_PROFILE_DATA = 'New Profile'
ADD_NEW_SHORTCUT = '+ New Shortcut'
ADD_NEW_SHORTCUT_DATA = 'New Shortcut'
BACK = '↩️ Back'
BACK_DATA = 'Back'
YES = 'Yes'
YES_DATA = 'Yes'
NO = 'No'
NO_DATA = 'No'

CHANGE_PASSWORD_LABEL = '🔑 Change Password'
CHANGE_PASSWORD_DATA = 'Change Password'
DELETE_PROFILE = '🗑️ Delete'
DELETE_PROFILE_DATA = 'Delete Profile'

DELETE_SHORTCUT = '🗑️ Delete'
DELETE_SHORTCUT_DATA = 'Delete Shortcut'

START_TRACKING = '✅ Start Tracking!'
RESERVE = '🎟 Reserve'
RESERVE_DATA = 'Reserve'
REFRESHED_TRACKING = '🔄 Refresh'
REFRESH_TRACKING_DATA = 'Refresh Tracking'
CANCEL_TRACKING = 'Cancel Tracking'
CANCEL_TRACKING_DATA = 'Cancel Tracking'
REFRESH_RESERVED = '🔄 Refresh'
REFRESH_RESERVED_DATA = 'Refresh Reserved'
CANCELLED_RESERVATION = 'Cancel Reservation'
CANCEL_RESERVATION_DATA = 'Cancel Reservation'

# Stages
(
    START,
    ADD_EMAIL, ADD_PASSWORD,
    PROFILE, SELECTED_PROFILE, CHANGE_PASSWORD,
    ADD_FROM_STATE, ADD_FROM_STATION,
    ADD_TO_STATE, ADD_TO_STATION,
    SHORTCUT, SELECTED_SHORTCUT,
    SET_EMAIL, SET_PASSWORD,
    SET_FROM_STATE, SET_FROM_STATION,
    SET_TO_STATE, SET_TO_STATION,
    SET_DATE,
    SET_TRIP,
    SET_TRACK,
    VIEW_TRACK,
    RESERVED,
    CLEAR
) = range(24)


class Title(Enum):
    CREATE_TRACKING = 'Creating new tracking...'
    # CREATE_TRACKING_FROM_STATE = '⬛⬛⬛⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_FROM_STATION = '🟩⬛⬛⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_TO_STATE = '🟩🟩⬛⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_TO_STATION = '🟩🟩🟩⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_DATE = '🟩🟩🟩🟩⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_TIME = '🟩🟩🟩🟩🟩⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_PRICE = '🟩🟩🟩🟩🟩🟩\n' + str(CREATE_TRACKING)
    CREATE_TRACKING_FROM_STATE = '🌑 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_FROM_STATION = '🌑 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_TO_STATE = '🌒 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_TO_STATION = '🌒 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_DATE = '🌓 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_TIME = '🌔 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_PRICE = '🌕 ' + str(CREATE_TRACKING)
    ADDED_TRACKING = '✅ New tracking added!'
    REFRESHED_TRACKING = '🔄 Tracking refreshed!'
    RESERVED = '🎟 New reservation made!'
    CANCELLED_RESERVATION = '❎ Reservation cancelled!'
    TRACKING_NUM = '🔍 Tracking '
    ADD_PROFILE = '👤 Adding new profile...'
    ADDED_PROFILE = '✅ New profile added!'
    MANAGE_PROFILE = '👤 Managing profile...'
    UPDATED_PROFILE = '✅ Profile updated!'
    DELETED_PROFILE = '❎ Profile deleted!'
    ADD_SHORTCUT = '🔀 Adding new shortcut...'
    ADDED_SHORTCUT = '✅ New shortcut added!'
    MANAGE_SHORTCUT = '👤 Managing shortcut...'
    DELETED_SHORTCUT = '❎ Shortcut deleted!'
