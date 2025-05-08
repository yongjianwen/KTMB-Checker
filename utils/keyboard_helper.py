from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, ReplyKeyboardMarkup

from .constants import (
    FROM_STATION_NAME, TO_STATION_NAME, TRACKING_UUID
)
from .constants import (
    TRACK_NEW_TRAIN, VIEW_TRACKING,
    ADD_NEW_PROFILE, ADD_NEW_PROFILE_DATA,
    ADD_NEW_SHORTCUT, ADD_NEW_SHORTCUT_DATA,
    BACK, BACK_DATA,
    YES, YES_DATA,
    NO, NO_DATA,
    CHANGE_PASSWORD_LABEL, CHANGE_PASSWORD_DATA,
    DELETE_PROFILE, DELETE_PROFILE_DATA,
    DELETE_SHORTCUT, DELETE_SHORTCUT_DATA,
    START_TRACKING,
    RESERVE, RESERVE_DATA,
    REFRESHED_TRACKING, REFRESH_TRACKING_DATA,
    CANCEL_TRACKING, CANCEL_TRACKING_DATA,
    REFRESH_RESERVED, REFRESH_RESERVED_DATA,
    CANCEL_RESERVATION, CANCEL_RESERVATION_DATA,
    Title
)
from .utils import get_number_emoji_from


def build_bottom_reply_markup():
    bottom_keyboard = [
        [TRACK_NEW_TRAIN, VIEW_TRACKING]
    ]
    return ReplyKeyboardMarkup(bottom_keyboard, one_time_keyboard=False, resize_keyboard=True)


def build_profiles_keyboard(profiles, prefix='', create=False):
    keyboard = []

    for email in profiles.keys():
        keyboard.append([InlineKeyboardButton(email, callback_data=prefix + email)])

    if create:
        keyboard.append([InlineKeyboardButton(ADD_NEW_PROFILE, callback_data=prefix + ADD_NEW_PROFILE_DATA)])

    return keyboard


def build_profile_actions_keyboard(email, prefix='', back=False):
    keyboard = [
        [
            InlineKeyboardButton(CHANGE_PASSWORD_LABEL, callback_data=f'{CHANGE_PASSWORD_DATA}/{email}')
        ],
        [
            InlineKeyboardButton(DELETE_PROFILE, callback_data=f'{DELETE_PROFILE_DATA}/{email}')
        ]
    ]

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_shortcuts_keyboard(shortcuts, prefix='', create=False):
    keyboard = []

    for key, value in shortcuts.items():
        keyboard.append([
            InlineKeyboardButton(
                value.get(FROM_STATION_NAME) + ' ➡️ ' + value.get(TO_STATION_NAME),
                callback_data=prefix + str(key)
            )
        ])

    if create:
        keyboard.append([InlineKeyboardButton(ADD_NEW_SHORTCUT, callback_data=prefix + ADD_NEW_SHORTCUT_DATA)])

    return keyboard


def build_shortcut_actions_keyboard(uuid, prefix='', back=False):
    keyboard = [
        [
            InlineKeyboardButton(DELETE_SHORTCUT, callback_data=f'{DELETE_SHORTCUT_DATA}/{uuid}')
        ]
    ]

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_states_keyboard(stations_data, shortcuts, prefix='', back=False):
    keyboard = []
    row = []

    for state in stations_data:
        button = InlineKeyboardButton(
            state.get('State'),
            callback_data=prefix + state.get('State')
        )

        if len(state.get('State')) < 10:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        else:
            if row:  # Add any accumulated buttons first
                keyboard.append(row)
                row = []
            keyboard.append([button])  # Add current button as new row

    # Add any remaining buttons in row
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
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_stations_keyboard(stations_data, state_selected, prefix='', back=False):
    keyboard = []
    row = []

    for station in next(state.get('Stations') for state in stations_data if state.get('State') == state_selected):
        button = InlineKeyboardButton(
            station.get('Description'),
            callback_data=prefix + station.get('Id')
        )

        if len(station.get('Description')) < 8:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        else:
            if row:
                keyboard.append(row)
                row = []
            keyboard.append([button])

    if row:
        keyboard.append(row)

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_dates_keyboard(prefix='', back=False):
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
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def next_friday(from_date):
    days_ahead = 4 - from_date.weekday()  # Friday is 4
    if days_ahead <= 0:  # Friday, Saturday, Sunday
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def build_times_keyboard(trips_data, prefix='', back=False):
    keyboard = []

    for index, trip in enumerate(trips_data):
        keyboard.append([
            InlineKeyboardButton(
                f'{trip.get('departure_time')} - {trip.get('arrival_time')} ({trip.get('available_seats')})',
                callback_data=prefix + str(index)
            )
        ])

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_tracking_prices_keyboard(prices, prefix='', back=False):
    keyboard = []

    for price in prices:
        keyboard.append([
            InlineKeyboardButton(f'{START_TRACKING} (RM {str(price)})', callback_data=prefix + str(price))
        ])

    keyboard.append([
        InlineKeyboardButton(f'{START_TRACKING} (Any Price)', callback_data=prefix + '-1')
    ])

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_tracked_actions_keyboard(uuid, prefix='', back=False):
    keyboard = [
        [
            InlineKeyboardButton(RESERVE, callback_data=f'{RESERVE_DATA}/{uuid}'),
            InlineKeyboardButton(REFRESHED_TRACKING, callback_data=f'{REFRESH_TRACKING_DATA}/{uuid}')
        ],
        [
            InlineKeyboardButton(CANCEL_TRACKING, callback_data=f'{CANCEL_TRACKING_DATA}/{uuid}')
        ]
    ]

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_view_trackings_keyboard(trackings, prefix=''):
    keyboard = []

    for index, t in enumerate(trackings):
        keyboard.append([
            InlineKeyboardButton(
                # f'{Title.TRACKING_NUM.value} {index + 1}',
                f'🔍 Tracking {get_number_emoji_from(index + 1)}',
                callback_data=prefix + str(t.get(TRACKING_UUID))
            )
        ])

    return keyboard


def build_reserved_actions_keyboard(uuid, prefix='', back=False):
    keyboard = [
        [
            InlineKeyboardButton(REFRESH_RESERVED, callback_data=f'{REFRESH_RESERVED_DATA}/{uuid}')
        ],
        [
            InlineKeyboardButton(CANCEL_RESERVATION, callback_data=f'{CANCEL_RESERVATION_DATA}/{uuid}')
        ]
    ]

    if back:
        keyboard.append([InlineKeyboardButton(BACK, callback_data=prefix + BACK_DATA)])

    return keyboard


def build_clear_actions_keyboard(prefix=''):
    keyboard = [
        [
            InlineKeyboardButton(NO, callback_data=prefix + NO_DATA),
            InlineKeyboardButton(YES, callback_data=prefix + YES_DATA)
        ]
    ]

    return keyboard
