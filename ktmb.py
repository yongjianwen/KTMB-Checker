import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from flask import Flask
from flask_cors import CORS
from requests.exceptions import RequestException

from config import email, password

# Custom start command (for Railway): gunicorn rates:app --bind 0.0.0.0:${PORT:-8000}
# Running at: sgd-myr-rates-api-production.up.railway.app:8080

app = Flask(__name__)

CORS(app, resources={r'/*': {
    'origins': [
        'http://yongjianwen-static.s3-website-ap-southeast-1.amazonaws.com',
        'http://127.0.0.1:5500'
    ]
}})

session = requests.Session()
token = ''
stations_data = []


@app.route('/ktmb')
def ktmb():
    try:
        login()
        print(
            get_seats(
                datetime(2025, 4, 18),
                *get_from_and_to_stations(
                    'JB Sentral',
                    'Bahau')
            )
        )
    except Exception as e:
        print(e)
    finally:
        logout()


def login():
    global token, stations_data

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
            'Email': email,
            'Password': password,
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
                    return True

        return False
    except RequestException as e:
        print(e)
        return False
    except AttributeError as e:
        print(e)
        return False


def get_from_and_to_stations(from_station_name, to_station_name):
    from_station = next(
        (
            {'StationData': station['StationData'], 'Id': station['Id']}
            for state in stations_data
            for station in state['Stations']
            if station['Description'].lower() == from_station_name.lower()
        )
        , None)

    to_station = next(
        (
            {'StationData': station['StationData'], 'Id': station['Id']}
            for state in stations_data
            for station in state['Stations']
            if station['Description'].lower() == to_station_name.lower()
        )
        , None)

    return from_station, to_station


def get_seats(trip_date, from_station, to_station):
    res = []

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

        trip_data = soup.find(lambda tag: tag.name == 'a' and tag.has_attr('data-tripdata')).get('data-tripdata')
        # print(trip_data)

        # 05 Get Seats
        url = 'https://online.ktmb.com.my/Trip/LayoutV2'
        headers = {'RequestVerificationToken': token}
        data = {
            'SearchData': search_data,
            'TripData': trip_data,
            'Pax': 1
        }
        r = session.post(url, headers=headers, json=data)
        coach_data = json.loads(r.content).get('Data').get('Coaches')
        # print(coach_data)

        # 0: Blocked
        # 1: Available
        # 2: Reserved
        # 3: Male
        # 4: Female or Male
        # 5: Not Shown

        for coach in coach_data:
            price = list(set(
                [
                    seat['Price'] for seat in coach.get('Seats') if
                    seat['Price'] != 0 and seat['Status'] == '1'
                ]
            ))
            res.append(
                {
                    coach.get('CoachLabel'): {
                        'SeatsLeft': coach.get('SeatAvailable'),
                        'Prices': price
                    }
                }
            )
    except RequestException as e:
        print(e)
    except AttributeError as e:
        print(e)

    return res


def logout():
    try:
        url = 'https://online.ktmb.com.my/Account/Logout'
        session.get(url)
    except RequestException as e:
        print(e)


def reserve(seat):
    pass


def cancel(seat):
    pass


if __name__ == '__main__':
    try:
        login()
        print(
            get_seats(
                datetime(2025, 4, 18),
                *get_from_and_to_stations(
                    'JB Sentral',
                    'Bahau')
            )
        )
    except Exception as ex:
        print(ex)
    finally:
        logout()
