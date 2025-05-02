import logging

from services.ktmb import get_seats

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
        'partial_content': contents,
        'seats_left_by_prices': res.get('seats_left_by_prices')
    }
