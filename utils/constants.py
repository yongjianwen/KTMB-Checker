from enum import Enum

# Regex
UUID_PATTERN = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
DATE_PATTERN = '\\d{4}-\\d{2}-\\d{2}'

# User data keys
COOKIE = 'cookie'
TOKEN = 'token'
LAST_MESSAGE = 'last_message'
STATE = 'state'
TO_STRIKETHROUGH = 'to_strikethrough'
TO_HIDE_KEYBOARD = 'to_hide_keyboard'

PROFILES = 'profiles'
SHORTCUTS = 'shortcuts'

TRANSACTION = 'transaction'
VOLATILE = 'volatile'
STATIONS_DATA = 'stations_data'
TRACKING_LIST = 'tracking_list'

# Transaction keys
FROM_STATE_NAME, TO_STATE_NAME = 'from_state_name', 'to_state_name'
FROM_STATION_ID, TO_STATION_ID = 'from_station_id', 'to_station_id'
FROM_STATION_NAME, TO_STATION_NAME = 'from_station_name', 'to_station_name'
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
BACK = '↩️ Back'
BACK_DATA = 'Back'

CHANGE_PASSWORD = 'Change Password'
CHANGE_PASSWORD_DATA = 'Change Password'
DELETE_PROFILE = 'Delete'
DELETE_PROFILE_DATA = 'Delete Profile'

DELETE_SHORTCUT = 'Delete'
DELETE_SHORTCUT_DATA = 'Delete Shortcut'

START_TRACKING = '✅ Start Tracking!'
RESERVE = '🎟 Reserve'
RESERVE_DATA = 'Reserve'
REFRESH_TRACKING = '🔄 Refresh'
REFRESH_TRACKING_DATA = 'Refresh Tracking'
CANCEL_TRACKING = 'Cancel Tracking'
CANCEL_TRACKING_DATA = 'Cancel Tracking'
REFRESH_RESERVED = '🔄 Refresh'
REFRESH_RESERVED_DATA = 'Refresh Reserved'
CANCEL_RESERVATION = 'Cancel Reservation'
CANCEL_RESERVATION_DATA = 'Cancel Reservation'

# Prefixes
# MANAGE_PROFILE = 'manage_profile'
# ADD_FROM_STATE =

# Commands
# START = 'start'
# ADD = 'add'
# MANAGE = 'manage'
# LOGIN = 'login'
# LOGOUT = 'logout'
# ADD_SHORTCUT = 'add_shortcut'
# MANAGE_SHORTCUT = 'manage_shortcut'
# CLEAR = 'clear'
# BACKUP = 'backup'


# Title states
class Title(Enum):
    CREATE = '📍 Creating new tracking...'
    NEW_TRACKING = '✅ New tracking added!'
    REFRESH_TRACKING = '✅ Tracking refreshed!'
    NEW_RESERVATION = '🎟 New reservation made!'
    CANCEL_RESERVATION = '✅ Reservation cancelled!'
    VIEW_TRACKING = '✴️ Tracking '
