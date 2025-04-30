import logging
from datetime import datetime

from services.ktmb import get_seats
from .constants import (
    FROM_STATION_NAME, FROM_STATE_NAME,
    TO_STATION_NAME, TO_STATE_NAME,
    DATE,
    DEPARTURE_TIME, ARRIVAL_TIME,
    PARTIAL_CONTENT,
    Title
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def get_station_by_id(stations_data, station_id):
    station = next(
        (
            {
                'Description': station.get('Description'),
                'StationData': station.get('StationData'),
                'Id': station.get('Id')
            }
            for state in stations_data
            for station in state.get('Stations', [])
            if station.get('Id') == station_id
        )
        , None)

    return station


async def get_seats_contents(search_data, trip_data, session, token):
    # logger.info(data)
    res = get_seats(
        session,
        search_data,
        trip_data,
        token
    )
    if not res.get('status'):
        return {
            'status': False,
            'error': res.get('error')
        }

    layout_data = res.get('layout_data')
    seats_data = res.get('seats_data')
    # logger.info(seats_data)

    contents = ''
    overall_prices = set()
    for coach in seats_data:
        line = f'{coach.get('CoachLabel')}: '
        seats_left = coach.get('CoachData').get('SeatsLeft')
        line += f'{seats_left} seats left'
        if seats_left != 0:
            line += ' ('
            for price in coach.get('CoachData').get('Prices'):
                line += f'RM {str(price)} / '
                overall_prices.add(price)
            line = line[:-3] + ')'
        contents += line + '\n'

    return {
        'status': True,
        'layout_data': layout_data,
        'seats_data': seats_data,
        'overall_prices': overall_prices,
        PARTIAL_CONTENT: contents,
        'seats_left_by_prices': res.get('seats_left_by_prices')
    }


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
