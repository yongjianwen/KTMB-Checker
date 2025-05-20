from datetime import datetime

from .constants import (
    FROM_STATION_NAME, FROM_STATE_NAME,
    TO_STATION_NAME, TO_STATE_NAME,
    DATE,
    DEPARTURE_TIME, ARRIVAL_TIME,
    PARTIAL_CONTENT,
    LAST_RUN, LAST_API_RUN
)
from .utils import get_weekday


def get_tracking_content(transaction, volatile, title):
    from_station_name = transaction.get(FROM_STATION_NAME)
    from_state_name = transaction.get(FROM_STATE_NAME)
    to_station_name = transaction.get(TO_STATION_NAME)
    to_state_name = transaction.get(TO_STATE_NAME)
    date_value = transaction.get(DATE)
    departure_time = transaction.get(DEPARTURE_TIME)
    arrival_time = transaction.get(ARRIVAL_TIME)
    partial_content = volatile.get(PARTIAL_CONTENT) or ''
    last_run_value = transaction.get(LAST_RUN)
    last_api_run_value = transaction.get(LAST_API_RUN)

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
    last_run = ''
    if last_run_value is not None:
        last_run = f'Last run: {last_run_value.strftime('%Y-%m-%d %H:%M:%S')}'
    last_api_run = ''
    if last_api_run_value is not None:
        last_api_run = f'Last API run: {last_api_run_value.strftime('%Y-%m-%d %H:%M:%S')}'

    message = (
        f'{title}'
        f'{'\n' if departure else ''}'
        f'{departure}'
        f'{destination}'
        f'{date}'
        f'{time}'
        f'{'\n' if partial_content else ''}'
        f'{partial_content}'
        f'{'\n' if last_run else ''}'
        f'{last_run}'
        f'{'\n' if last_api_run else ''}'
        f'{last_api_run}'
    )

    return message


def get_seats_left_by_prices_content(prev, cur):
    message = '<b><u>Seats Left by Price(s)</u></b>\n'
    keys_to_remove = []
    for key, value in prev.items():
        if key in cur:
            message = message + f'RM {key}: {value} ➡️ {cur.get(key)}\n'
            keys_to_remove.append(key)

    for key in keys_to_remove:
        prev.pop(key, None)
        cur.pop(key, None)

    for key, value in prev.items():
        message = message + f'RM {key}: {value} ➡️ 0\n'

    for key, value in cur.items():
        message = message + f'RM {key}: 0 ➡️ {value}\n'

    return message
