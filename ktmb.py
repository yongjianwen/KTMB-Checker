import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
# from flask import Flask
# from flask_cors import CORS
from requests.exceptions import RequestException

load_dotenv()  # Loads variables from .env

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')


# app = Flask(__name__)

# CORS(app, resources={r'/*': {
#     'origins': [
#         'http://yongjianwen-static.s3-website-ap-southeast-1.amazonaws.com',
#         'http://127.0.0.1:5500'
#     ]
# }})

# session = requests.Session()  # May be expired in 30 days


# @app.route('/ktmb')
# def ktmb():
#     main()


def login(session, debug=False):
    if debug:
        return {
            'status': True,
            'token': 'abc',
            'stations_data': []
        }

    try:
        # 01 Login
        url = 'https://online.ktmb.com.my/Account/Login'
        r = session.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')

        token = soup.find('input', attrs={'name': '__RequestVerificationToken'}).get('value')
        # print(token)

        # 02 Login
        data = {
            'RedirectData': '',
            'ReturnUrl': '',
            'Email': EMAIL,
            'Password': PASSWORD,
            '__RequestVerificationToken': token,
            'SubmitValue': 'Login'
        }
        r = session.post(url, data=data)
        soup = BeautifulSoup(r.content, 'html.parser')

        token = soup.find('input', attrs={'name': '__RequestVerificationToken'}).get('value')
        # print(token)

        script_tags = soup.find_all('script', attrs={'type': 'text/javascript'})

        for script_tag in script_tags:
            script_content = script_tag.string
            # print(script_content)
            # print('---------------------------------------------------------------------')

            grouped_stations_match = re.search(r'var\s+groupedStations\s*=\s*(\[\s*{.*?}\s*]);', script_content,
                                               re.DOTALL)
            if grouped_stations_match:
                grouped_stations_data = json.loads(grouped_stations_match.group(1))
                # print('Grouped Stations:', grouped_stations_data)

                js_stations_match = re.search(r'var\s+jsStations\s*=\s*(\[\s*{.*?}\s*]);', script_content, re.DOTALL)
                if js_stations_match:
                    js_stations_data = json.loads(js_stations_match.group(1))
                    # print('JS Stations:', js_stations_data)

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
                    # print('Merged Stations:', stations_data)

                    print('>> Logged in successfully')
                    return {
                        'status': True,
                        'token': token,
                        'stations_data': stations_data
                    }
    except Exception as e:
        print(e)
    # except RequestException as e:
    #     print(e)
    # except AttributeError as e:
    #     print(e)

    print('>> Log in error')
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

        for script_tag in script_tags:
            script_content = script_tag.string
            # print(script_content)
            # print('---------------------------------------------------------------------')

            grouped_stations_match = re.search(r'var\s+groupedStations\s*=\s*(\[\s*{.*?}\s*]);', script_content,
                                               re.DOTALL)
            if grouped_stations_match:
                grouped_stations_data = json.loads(grouped_stations_match.group(1))
                # print('Grouped Stations:', grouped_stations_data)

                js_stations_match = re.search(r'var\s+jsStations\s*=\s*(\[\s*{.*?}\s*]);', script_content, re.DOTALL)
                if js_stations_match:
                    js_stations_data = json.loads(js_stations_match.group(1))
                    # print('JS Stations:', js_stations_data)

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
                    # print('Merged Stations:', stations_data)

                    print('>> Get stations successfully')
                    return {
                        'status': True,
                        'stations_data': stations_data
                    }
    except Exception as e:
        print(e)

    return {
        'status': False,
        'error': 'Get stations error'
    }


# def get_from_and_to_stations(from_station_name, to_station_name):
#     from_station = next(
#         (
#             {'StationData': station['StationData'], 'Id': station['Id']}
#             for state in stations_data
#             for station in state['Stations']
#             if station['Description'].lower() == from_station_name.lower()
#         )
#         , None)
#
#     to_station = next(
#         (
#             {'StationData': station['StationData'], 'Id': station['Id']}
#             for state in stations_data
#             for station in state['Stations']
#             if station['Description'].lower() == to_station_name.lower()
#         )
#         , None)
#
#     return from_station, to_station


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

        search_data = soup.find(id='SearchData').get('value')
        # print(search_data)
        form_validation_code = soup.find(id='FormValidationCode').get('value')
        # print(form_validation_code)

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
        # print(r.content)
        soup = BeautifulSoup(r.content, 'html.parser')
        soup = BeautifulSoup(json.loads(str(soup))['data'], 'html.parser')
        # print(soup)

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
        # print(trips_data)

        print('>> Get trips successfully')
        return {
            'status': True,
            'search_data': search_data,
            'trips_data': trips_data
        }
    except Exception as e:
        print(e)

    print('>> Get trips error')
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
        json_data = json.loads(r.content).get('Data')
        # print(json_data)

        layout_data = json_data.get('LayoutData')
        # print(layout_data)
        coach_data = json_data.get('Coaches')
        # print(coach_data)

        # 0: Blocked
        # 1: Available
        # 2: Reserved
        # 3: Male
        # 4: Female or Male
        # 5: Not Shown

        seats_data = []
        for coach in coach_data:
            seats = [
                # {
                #     'Price': seat['Price'],
                #     'SeatIndex': seat['SeatIndex'],
                #     'SeatNo': seat['SeatNo'],
                #     'SeatType': seat['SeatType'],
                #     'SeatTypeName': seat['SeatTypeName'],
                #     'ServiceType': seat['ServiceType'],
                #     'Status': seat['Status'],
                #     'Surcharge': seat['Surcharge'],
                #     'SeatData': seat['SeatData']
                # }
                seat for seat in coach['Seats'] if seat['Status'] == '1'
            ]
            prices = [
                price for price in set([seat['Price'] for seat in seats])
            ]
            seats_data.append(
                {
                    'CoachLabel': coach.get('CoachLabel'),
                    'CoachData': {
                        'SeatsLeft': coach.get('SeatAvailable'),
                        'Prices': prices,
                        'Seats': seats
                    }
                }
            )

        print('>> Get seats successfully')
        return {
            'status': True,
            'layout_data': layout_data,
            'seats_data': seats_data
        }
    except Exception as e:
        print(e)

    print('>> Get seats error')
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
        # print(r.content)

        print('>> Reserved successfully')
        return {
            'status': True,
            'booking_data': booking_data
        }
    except Exception as e:
        print(e)

    print('>> Reserve error')
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
        # print(status)

        print('>> Cancel successfully')
        return {
            'status': status
        }
    except Exception as e:
        print(e)

    print('>> Cancel error')
    return {
        'status': False,
        'error': 'Cancel error'
    }


def logout(session):
    try:
        url = 'https://online.ktmb.com.my/Account/Logout'
        session.get(url)

        print('>> Logout executed')
        return {
            'status': True
        }
    except RequestException as e:
        print(e)

    print('>> Logout error')
    return {
        'status': False,
        'error': 'Logout error'
    }


def main():
    session = requests.Session()

    try:
        login_res = login(session)
        if not login_res.get('status'):
            raise Exception(login_res.get('error'))

        _token = login_res.get('token')
        _stations_data = login_res.get('stations_data')

        trips_res = get_trips(
            session,
            datetime(2025, 4, 18),
            get_station_by_id(_stations_data, '37500'),
            get_station_by_id(_stations_data, '27800'),
            _token
        )
        if not trips_res.get('status'):
            raise Exception(trips_res.get('error'))

        _search_data = trips_res.get('search_data')
        _trips_data = json.loads(json.dumps(trips_res.get('trips_data')))

        _trip_data = next(t['trip_data'] for t in _trips_data if int(t['available_seats']) > 0)

        seats_res = get_seats(
            session,
            _search_data,
            _trip_data,
            _token
        )
        if not seats_res.get('status'):
            raise Exception(seats_res.get('error'))

        _layout_data = seats_res.get('layout_data')
        _seats_data = seats_res.get('seats_data')
        # print('\n'.join([str(s) for s in _seats_data]))

        # reserve_res = reserve_by_price(
        #     _seats_data,
        #     int(input('Enter price of ticket to reserve: ')),
        #     _search_data,
        #     _trip_data,
        #     _layout_data,
        #     _token
        # )
        # if not reserve_res.get('status'):
        #     raise Exception(reserve_res.get('error'))
        #
        # _booking_data = reserve_res.get('booking_data')
        #
        # input('Enter any character to cancel reservation: ')
        #
        # cancel_res = cancel(_search_data, _booking_data, _token)
        # if not cancel_res.get('status'):
        #     raise Exception(cancel_res.get('error'))
    except Exception as ex:
        print(ex)
    finally:
        logout(session)


if __name__ == '__main__':
    main()
