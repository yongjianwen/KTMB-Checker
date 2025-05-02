from datetime import datetime

from .constants import (
    FROM_STATION_NAME, FROM_STATE_NAME,
    TO_STATION_NAME, TO_STATE_NAME,
    DATE,
    DEPARTURE_TIME, ARRIVAL_TIME,
    PARTIAL_CONTENT
)


def get_tracking_content(transaction, volatile, title):
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
