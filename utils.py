from datetime import timedelta, datetime
from enum import Enum

from telegram import InlineKeyboardButton

#
UUID_PATTERN = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

# Inline keyboard
BACK_LABEL = '↩️ Back'
BACK_DATA = 'Back'

# User data
COOKIE = 'cookie'
TOKEN = 'token'
LAST_MESSAGE = 'last_message'
TO_STRIKETHROUGH = 'to_strikethrough'
TO_HIDE_KEYBOARD = 'to_hide_keyboard'
STATIONS_DATA = 'stations_data'
FROM_STATE_NAME, TO_STATE_NAME = 'from_state_name', 'to_state_name'
FROM_STATION_ID, TO_STATION_ID = 'from_station_id', 'to_station_id'
FROM_STATION_NAME, TO_STATION_NAME = 'from_station_name', 'to_station_name'
DATE = 'date'
PARTIAL_CONTENT = 'partial_content'

#
SEARCH_DATA = 'search_data'
TRIPS_DATA = 'trips_data'
# TRIP_DATA_INDEX = 'trip_data_index'
TRIP_DATA = 'trip_data'
DEPARTURE_TIME = 'departure_time'
ARRIVAL_TIME = 'arrival_time'
LAYOUT_DATA = 'layout_data'
PRICE = 'price'
TRACKING_LIST = 'tracking_list'
RESERVED_SEAT = 'reserved_seat'


# Title states
class Title(Enum):
    CREATE = '📍 Creating new tracking...'
    NEW_TRACKING = '✅ New tracking added!'
    REFRESH_TRACKING = '✅ Tracking refreshed!'
    NEW_RESERVATION = '🎟 New reservation made!'
    CANCEL_RESERVATION = '✅ Reservation cancelled!'
    VIEW = '✴️ Tracking '


def build_profile_keyboard(profiles, prefix=''):
    keyboard = []

    for email in profiles.keys():
        keyboard.append([
            InlineKeyboardButton(
                email,
                callback_data=prefix + email
            )
        ])

    return keyboard


def build_manage_profile_keyboard(email, prefix=''):
    keyboard = [
        [
            # InlineKeyboardButton('🎟 Reserve', callback_data=f'Reserve/{uuid}'),
            InlineKeyboardButton('Change Password', callback_data=f'Change Password/{email}')
        ],
        [
            InlineKeyboardButton('Delete', callback_data=f'Delete/{email}')
        ]
    ]

    return keyboard


def build_shortcut_keyboard(shortcuts, prefix=''):
    keyboard = []

    for key, value in shortcuts.items():
        keyboard.append([
            InlineKeyboardButton(
                value.get(FROM_STATION_NAME) + ' ➡️ ' + value.get(TO_STATION_NAME),
                callback_data=prefix + str(key)
            )
        ])

    return keyboard


def build_manage_shortcut_keyboard(shortcut_uuid, prefix=''):
    keyboard = [
        [
            InlineKeyboardButton('Delete', callback_data=f'Delete Shortcut/{shortcut_uuid}')
        ]
    ]

    return keyboard


def build_state_keyboard(stations_data, shortcuts, prefix='', back=False):
    keyboard = []
    row = []

    for state in stations_data:
        button = InlineKeyboardButton(
            state['State'],
            callback_data=prefix + state['State']
        )

        if len(state['State']) < 10:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        else:
            if row:  # Add any accumulated buttons first
                keyboard.append(row)
                row = []
            keyboard.append([button])  # Add current button as new row

    # Add any remaining buttons in temp_row
    if row:
        keyboard.append(row)

    for key, value in shortcuts.items():
        keyboard.append([
            InlineKeyboardButton(
                value.get(FROM_STATION_NAME) + ' ➡️ ' + value.get(TO_STATION_NAME),
                callback_data=prefix + str(key)
            )
        ])

    if back:
        keyboard.append([
            InlineKeyboardButton(BACK_LABEL, callback_data=prefix + BACK_DATA)
        ])

    return keyboard


def generate_station_keyboard(stations_data, state_selected, prefix='', back=False):
    keyboard = []
    row = []

    for station in next(state['Stations'] for state in stations_data if state['State'] == state_selected):
        button = InlineKeyboardButton(
            station['Description'],
            callback_data=prefix + station['Id']
        )

        if len(station['Description']) < 8:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        else:
            if row:  # Add any accumulated buttons first
                keyboard.append(row)
                row = []
            keyboard.append([button])  # Add current button as new row

    # Add any remaining buttons in temp_row
    if row:
        keyboard.append(row)

    if back:
        keyboard.append([
            InlineKeyboardButton(BACK_LABEL, callback_data=prefix + BACK_DATA)
        ])

    return keyboard


def generate_friday_keyboard(prefix='', back=False):
    keyboard = []

    today = datetime.today()
    today_str = today.strftime('%Y-%m-%d')

    f1 = next_friday(today)
    f1_str = f1.strftime('%Y-%m-%d')

    f2 = next_friday(f1)
    f2_str = f2.strftime('%Y-%m-%d')

    f3 = next_friday(f2)
    f3_str = f3.strftime('%Y-%m-%d')

    if today.weekday() == 4:  # Friday
        keyboard.extend([
            [InlineKeyboardButton(f'Today ({today_str})', callback_data=prefix + today_str)],
            [InlineKeyboardButton(f'Next Friday ({f1_str})', callback_data=prefix + f1_str)],
            [InlineKeyboardButton(f'Next Next Friday ({f2_str})', callback_data=prefix + f2_str)]
        ])
    elif today.weekday() == 5:  # Saturday
        keyboard.extend([
            [InlineKeyboardButton(f'Next Friday ({f1_str})', callback_data=prefix + f1_str)],
            [InlineKeyboardButton(f'Next Next Friday ({f2_str})', callback_data=prefix + f2_str)],
            [InlineKeyboardButton(f'Next Next Next Friday ({f3_str})', callback_data=prefix + f3_str)]
        ])
    else:  # Sunday - Thursday
        keyboard.extend([
            [InlineKeyboardButton(f'This Friday ({f1_str})', callback_data=prefix + f1_str)],
            [InlineKeyboardButton(f'Next Friday ({f2_str})', callback_data=prefix + f2_str)],
            [InlineKeyboardButton(f'Next Next Friday ({f3_str})', callback_data=prefix + f3_str)]
        ])

    if back:
        keyboard.append([
            InlineKeyboardButton(BACK_LABEL, callback_data=prefix + BACK_DATA)
        ])

    return keyboard


def next_friday(from_date):
    days_ahead = 4 - from_date.weekday()  # Friday is 4
    if days_ahead <= 0:  # Friday, Saturday, Sunday
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def generate_trips_keyboard(trips_data, prefix='', back=False):
    keyboard = []

    for index, trip in enumerate(trips_data):
        keyboard.append([
            InlineKeyboardButton(
                # f'{trip.get('departure_time')} ➡️ {trip.get('arrival_time')} ({trip.get('available_seats')})',
                f'{trip.get('departure_time')} - {trip.get('arrival_time')} ({trip.get('available_seats')})',
                callback_data=prefix + str(index)
            )
        ])

    if back:
        keyboard.append([
            InlineKeyboardButton(BACK_LABEL, callback_data=prefix + BACK_DATA)
        ])

    return keyboard


def generate_tracking_keyboard(prices, prefix='', back=False):
    keyboard = []

    for price in prices:
        print(prefix + str(price))
        keyboard.append([
            InlineKeyboardButton(f'✅ Start Tracking! (RM {str(price)})', callback_data=prefix + str(price))
        ])

    keyboard.append([
        InlineKeyboardButton(f'✅ Start Tracking! (Any Price)', callback_data=prefix + '-1')
    ])

    if back:
        keyboard.append([
            InlineKeyboardButton(BACK_LABEL, callback_data=prefix + BACK_DATA)
        ])

    return keyboard


def generate_reserve_keyboard(uuid):
    keyboard = [
        [
            # InlineKeyboardButton('🎟 Reserve', callback_data=f'Reserve/{uuid}'),
            InlineKeyboardButton('🔄 Refresh', callback_data=f'Refresh/{uuid}')
        ],
        [
            InlineKeyboardButton('Cancel Tracking', callback_data=f'Cancel Tracking/{uuid}')
        ]
    ]

    return keyboard


def generate_reserved_keyboard(uuid):
    keyboard = [
        [
            InlineKeyboardButton('🔄 Refresh', callback_data=f'Refresh Reserved/{uuid}')
        ],
        [
            InlineKeyboardButton('Cancel Reservation', callback_data=f'Cancel Reservation/{uuid}')
        ]
    ]

    return keyboard


def get_tracking_content(transaction, volatile, title=Title.CREATE.value):
    from_station_name = transaction.get(FROM_STATION_NAME)
    from_state_name = transaction.get(FROM_STATE_NAME)
    to_station_name = transaction.get(TO_STATION_NAME)
    to_state_name = transaction.get(TO_STATE_NAME)
    date_value = transaction.get(DATE)
    departure_time = transaction.get(DEPARTURE_TIME)
    arrival_time = transaction.get(ARRIVAL_TIME)
    partial_content = volatile.get(PARTIAL_CONTENT) or ''

    title = f'<b>{title}</b>\n'
    departure = '' if from_state_name is None else (
            'Departure: <b>' +
            (f'{from_station_name}, ' if from_station_name is not None else '') + from_state_name + '</b>\n'
    )
    destination = '' if to_state_name is None else (
            'Destination: <b>' +
            (f'{to_station_name}, ' if to_station_name is not None else '') + to_state_name + '</b>\n'
    )
    date = ''
    if date_value is not None:
        weekday = get_weekday(datetime.strptime(date_value, '%Y-%m-%d').weekday())
        date = f'Date: <b>{date_value} ({weekday})</b>\n'
    time = '' if departure_time is None and arrival_time is None else (
        f'Time: <b>{departure_time} - {arrival_time}</b>\n'
    )

    message = (
        f'{title}'
        f'{'\n' if departure else ''}'
        f'{departure}'
        f'{destination}'
        f'{date}'
        f'{time}'
        f'{'\n' if partial_content else ''}'
        f'{partial_content}'
    )

    return message


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
