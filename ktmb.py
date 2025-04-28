import json
import logging
import re

from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def login(session, email, password):
    try:
        # 01 Login
        url = 'https://online.ktmb.com.my/Account/Login'
        r = session.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')

        token = soup.find('input', attrs={'name': '__RequestVerificationToken'}).get('value')

        # 02 Login
        data = {
            'RedirectData': '',
            'ReturnUrl': '',
            'Email': email,
            'Password': password,
            '__RequestVerificationToken': token,
            'SubmitValue': 'Login'
        }
        r = session.post(url, data=data)
        soup = BeautifulSoup(r.content, 'html.parser')
        # logger.info(soup)

        token = soup.find('input', attrs={'name': '__RequestVerificationToken'}).get('value')

        script_tags = soup.find_all('script', attrs={'type': 'text/javascript'})

        res = get_stations_data_from_script_tags(script_tags)
        if res.get('status'):
            return {
                'status': True,
                'token': token
            }
    except Exception as e:
        logger.info(e)

    logger.info('>> Log in error')
    return {
        'status': False,
        'error': 'Login error'
    }


def get_stations(session):
    try:
        url = 'https://online.ktmb.com.my'
        r = session.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')

        script_tags = soup.find_all('script', attrs={'type': 'text/javascript'})

        res = get_stations_data_from_script_tags(script_tags)
        if res.get('status'):
            return {
                'status': True,
                'stations_data': res.get('stations_data')
            }
    except Exception as e:
        logger.info(e)

    return {
        'status': False,
        'error': 'Get stations error'
    }


def get_stations_data_from_script_tags(script_tags):
    for script_tag in script_tags:
        script_content = script_tag.string

        grouped_stations_match = re.search(r'var\s+groupedStations\s*=\s*(\[\s*{.*?}\s*]);', script_content,
                                           re.DOTALL)
        if grouped_stations_match:
            grouped_stations_data = json.loads(grouped_stations_match.group(1))
            # logger.info('Grouped Stations:', grouped_stations_data)

            js_stations_match = re.search(r'var\s+jsStations\s*=\s*(\[\s*{.*?}\s*]);', script_content, re.DOTALL)
            if js_stations_match:
                js_stations_data = json.loads(js_stations_match.group(1))
                # logger.info('JS Stations:', js_stations_data)

                stations_data = [
                    {
                        **state,
                        'Stations': [
                            {
                                **station,
                                'StationData': next(
                                    s['StationData'] for s in js_stations_data if s['Id'] == station['Id'])
                            }
                            for station in state['Stations']
                        ]
                    }
                    for state in grouped_stations_data
                ]
                # logger.info('Merged Stations:', stations_data)

                logger.info('>> Get stations successfully')
                return {
                    'status': True,
                    'stations_data': stations_data
                }

    return {
        'status': False,
        'error': 'Get stations error'
    }


def get_station_by_id(stations_data, station_id):
    station = next(
        (
            {'Description': station['Description'], 'StationData': station['StationData'], 'Id': station['Id']}
            for state in stations_data
            for station in state['Stations']
            if station['Id'] == station_id
        )
        , None)

    return station


def get_trips(session, trip_date, from_station, to_station, token):
    try:
        # 03 Get Trip
        url = 'https://online.ktmb.com.my/Trip'
        headers = {'Referer': 'https://online.ktmb.com.my/'}
        data = {
            'FromStationData': from_station['StationData'],
            'ToStationData': to_station['StationData'],
            'FromStationId': from_station['Id'],
            'ToStationId': to_station['Id'],
            'OnwardDate': trip_date.strftime('%d %b %Y').lstrip('0'),
            'ReturnDate': '',
            'PassengerCount': 1,
            '__RequestVerificationToken': token
        }
        r = session.post(url, headers=headers, data=data)
        soup = BeautifulSoup(r.content, 'html.parser')
        # with open('response.txt', 'w') as f:
        #     f.write(str(soup))

        oops = soup.select('div.oops')
        # logger.info('oops:', str(oops))
        if len(oops) > 0:
            logger.info('>> Get trips error - log in related')
            return {
                'status': False,
                'error': 'Get trips error = log in related',
                'retry': True
            }
        search_data = soup.find(id='SearchData').get('value')
        form_validation_code = soup.find(id='FormValidationCode').get('value')

        # 04 Get Trip Trip
        url = 'https://online.ktmb.com.my/Trip/Trip'
        headers = {'RequestVerificationToken': token}
        data = {
            'SearchData': search_data,
            'FormValidationCode': form_validation_code,
            'DepartDate': trip_date.strftime('%Y-%m-%d'),
            'IsReturn': False,
            'BookingTripSequenceNo': 1
        }
        r = session.post(url, headers=headers, json=data)
        soup = BeautifulSoup(r.content, 'html.parser')
        # with open('response2.txt', 'w') as f:
        #     f.write(str(soup))
        soup = BeautifulSoup(json.loads(str(soup))['data'], 'html.parser')

        trip_rows = soup.find('tbody').find_all('tr')
        trips_data = []
        for trip_row in trip_rows:
            tds = trip_row.find_all('td')
            overnight = tds[2].find('span') is not None
            trips_data.append(
                {
                    'train_service': tds[0].get_text(strip=True),
                    'departure_time': tds[1].get_text(strip=True),
                    'arrival_time': ''.join(text for text in tds[2].find_all(text=True, recursive=False)).strip()
                                    + ('(+1)' if overnight else ''),
                    'available_seats': tds[4].get_text(strip=True),
                    'trip_data': tds[6].find('a').get('data-tripdata')
                }
            )
        # logger.info(trips_data)

        logger.info('>> Get trips successfully')
        return {
            'status': True,
            'search_data': search_data,
            'trips_data': trips_data
        }
    except Exception as e:
        logger.info(e)

    logger.info('>> Get trips error')
    return {
        'status': False,
        'error': 'Get trips error'
    }


def get_seats(session, search_data, trip_data, token):
    try:
        # 05 Get Seats
        url = 'https://online.ktmb.com.my/Trip/LayoutV2'
        headers = {'RequestVerificationToken': token}
        data = {
            'SearchData': search_data,
            'TripData': trip_data,
            'Pax': 1
        }
        r = session.post(url, headers=headers, json=data)
        # logger.info(r.content)
        json_data = json.loads(r.content).get('Data')
        # logger.info(json_data)

        layout_data = json_data.get('LayoutData')
        # logger.info(layout_data)
        coach_data = json_data.get('Coaches')
        # logger.info(coach_data)

        # 0: Blocked
        # 1: Available
        # 2: Reserved
        # 3: Male
        # 4: Female or Male
        # 5: Not Shown

        seats_data = []
        seats_left_by_prices = {}
        for coach in coach_data:
            seats = []
            prices = set()
            for seat in coach.get('Seats'):
                if seat.get('Status') == '1':
                    prices.add(seat.get('Price'))
                    seats.append(seat)
                    price_str = str(seat.get('Price'))
                    seats_left_by_prices[price_str] = seats_left_by_prices.get(price_str, 0) + 1

            seats_data.append(
                {
                    'CoachLabel': coach.get('CoachLabel'),
                    'CoachData': {
                        'SeatsLeft': len(seats),
                        'Prices': prices,
                        'Seats': seats
                    }
                }
            )

        logger.info('>> Get seats successfully')
        return {
            'status': True,
            'layout_data': layout_data,
            'seats_data': seats_data,
            'seats_left_by_prices': seats_left_by_prices
        }
    except Exception as e:
        logger.info(e)

    logger.info('>> Get seats error')
    return {
        'status': False,
        'error': 'Get seats error'
    }


def reserve_by_price(session, seats_data, price, search_data, trip_data, layout_data, token):
    for seat_data in seats_data:
        if seat_data.get('CoachData').get('SeatsLeft') > 0 and (
                price in seat_data.get('CoachData').get('Prices') or price == -1
        ):
            available_seats = seat_data.get('CoachData').get('Seats')
            for available_seat in available_seats:
                if available_seat.get('Price') == price or price == -1:
                    res = reserve(session, search_data, trip_data, layout_data, available_seat.get('SeatData'), token)
                    if res.get('status'):
                        return {
                            **res,
                            'CoachLabel': seat_data.get('CoachLabel'),
                            'SeatNo': available_seat.get('SeatNo'),
                            'Price': available_seat.get('Price'),
                            'SeatIndex': available_seat.get('SeatIndex')
                        }

    return {
        'status': False,
        'error': 'Reserve by price error'
    }


def reserve(session, search_data, trip_data, layout_data, seat_data, token):
    try:
        # 06 Reserve Seat
        url = 'https://online.ktmb.com.my/Trip/Reserve'
        headers = {'RequestVerificationToken': token}
        data = {
            'BookingData': '',
            'SearchData': search_data,
            'Trips': [
                {
                    'TripData': trip_data,
                    'LayoutData': layout_data,
                    'Seats': [
                        {
                            'SeatData': seat_data
                        }
                    ]
                }
            ]
        }
        r = session.post(url, headers=headers, json=data)
        booking_data = json.loads(r.content).get('data').get('bookingData')
        # logger.info(r.content)

        logger.info('>> Reserved successfully')
        return {
            'status': True,
            'booking_data': booking_data
        }
    except Exception as e:
        logger.info(e)

    logger.info('>> Reserve error')
    return {
        'status': False,
        'error': 'Reserve error'
    }


def cancel_reservation(session, search_data, booking_data, token):
    try:
        # 07 Cancel Reservation
        url = 'https://online.ktmb.com.my/Book/Cancel'
        headers = {'RequestVerificationToken': token}
        data = {
            'BookingData': booking_data,
            'SearchData': search_data,
        }
        r = session.post(url, headers=headers, json=data)
        status = json.loads(r.content).get('status')
        # logger.info(status)

        logger.info('>> Cancel successfully')
        return {
            'status': status
        }
    except Exception as e:
        logger.info(e)

    logger.info('>> Cancel error')
    return {
        'status': False,
        'error': 'Cancel error'
    }


def logout(session):
    try:
        url = 'https://online.ktmb.com.my/Account/Logout'
        session.get(url)

        logger.info('>> Logout executed')
        return {
            'status': True
        }
    except RequestException as e:
        logger.info(e)

    logger.info('>> Logout error')
    return {
        'status': False,
        'error': 'Logout error'
    }
