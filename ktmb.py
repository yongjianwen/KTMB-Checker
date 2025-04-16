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

session = requests.Session()  # May be expired in 30 days
debug_stations_data = [
    {'State': 'Kedah', 'Stations': [
        {'Description': 'ALOR SETAR', 'Id': '44000', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': '4dowiuHMnQUcITyW1bJ4Vl0/NSJ8I1PUtT2Qnq4cnuKGI04AX1OKDSgcFo4bFfRFDZ7c4BpxXqEar0wpEe02Xm5JyO7RlXNugJzgDdUwFwYg3ASZSftFI30w114WQZAn7uj3OZy21SRCFpVpGwALitAn02FgmvaeIgsZCMBn9fs='},
        {'Description': 'ANAK BUKIT', 'Id': '44400', 'TrainServices': ['ETS'],
         'StationData': 'l2IrQiI4C+GS1JPLZ3SeoJRfVRtNiG6OradTSjSK8TilL+4jSMw2i2oxb8R9PozQ3j4WYj2ETifePluMTSKSYi5Y8GmjLqhZaLNOvuf9Z9r3gzpdkNf7g8KEFM/9igh/NcJUfohI0FeWudIUG6i7gw=='},
        {'Description': 'GURUN', 'Id': '42400', 'TrainServices': ['ETS'],
         'StationData': 'S3gzOSbvz1scaZCwFBZwAm2xdj6MWW22QfPfwT5sQF82JTZSe006eprOWKj6skJ6tTDSYBhX2yy4zEr2E0JXvTyTEAjYKpgIwpH4oU6CBaFBbXFWMJ+X7wpC3gRFMry5'},
        {'Description': 'SUNGAI PETANI', 'Id': '41400', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': '2CRXi/SH7TX8AxsC1wcT2mOvTZy37AJYmE2TcxMdSpA0oljYPLMAc5NtaDQ7Y7gUPL3XIR5N2PuxcFldSErvkcGMU/xVVxpAxn1hCS3+uIbPFejvK00DeLZAWtmdcv9i1tzIA4Tr0b/3Evba9chwilXIEQnVhpW2rwoTeybp2BE='}]},
    {'State': 'Perlis', 'Stations': [
        {'Description': 'ARAU', 'Id': '45800', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': '8Gnp2RP0zMbsATP54S1Vtl0NUsKcy/uW7fWJEYwGON2koA6DXOxKCH71VT2x/zteLvDlnxaklRKoQ9o9G3GzAiS8NHhgWk5Y3b3VAhXURvIb6XgzNoG5cRfPnPi+uJx1e1sT0QBmSp+9nKpMpBzIQVbUn994qmUxzSuMIyGz+S4='},
        {'Description': 'PADANG BESAR', 'Id': '47300', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': 'SigT7x5FOR5VRP57JVTTaGYXNrvGntS2hN4aNKoiURJHMdyG+6lWTy9BToE4NBOkANALJwYzBgVTHycryhckBazAzJ6lYNcJLQvtvIBDySepk9Tgx4AQS63eLFA+928cS3C+xfgw6rCzcnBIoSHDVp17g/jeL8gpoBVzN6Wh2Fk='}]},
    {'State': 'Pahang', 'Stations': [
        {'Description': 'AUR GADING', 'Id': '72700', 'TrainServices': ['Intercity'],
         'StationData': 'fxZtdhKwwsLBpdx4u9RdE5ou4fBS7bqIcsBRZobjMt2i8KmLQ2b8BMgoP+XMV2gY0T4bcLbFRDMz9R+NXr/gjhxbaV1GgoAWT0sp5xr7JhhctGozoPfc4B0uzrLP74SHaNYcuWflV1j0mTfVg9goFw=='},
        {'Description': 'BUKIT BETONG', 'Id': '72200', 'TrainServices': ['Intercity'],
         'StationData': '/+Wwaf+Kc0gQxMbGBKB12njwDv350YgNXLTf+siVSQwXxogh3HolBuIKlipWtGWbLM/phwdjq4XOzRZYb+5grJ4ahIo1dn5q8qaWe/zoLmlKX/AZk5ZHUB7XijX8OA8BKwGN5f9+2sE9HAKa9R8pug=='},
        {'Description': 'CHEGAR PERAH', 'Id': '73100', 'TrainServices': ['Intercity'],
         'StationData': 'ame4B0d2CMmMbqBmamJ3OrGMNHdKNtkxX+Uy9Ja6vyAf2Xf/BwAKmTxRX/jPAy7mrYfgSWlkW2ajNGH9IH8z+3rZbmCfk3UaF4IS0aMyN0Jne9Df3UcS7CAygj5NRmb5oaTao5Fdjy2rMjP9qYrGwA=='},
        {'Description': 'JENDERAK', 'Id': '67900', 'TrainServices': ['Intercity'],
         'StationData': 'ShcbjVx6LJwhIqcKdPzAG/V6eO+rWwFSwPEAUQXTsSPo5f9r3rXh3+/3+olSkHgH0gAhQap9ZoyO15yp1sKOHVNMGW1kcwpVeLH5YSIiP1V7AHgJJySp1nqKR5NJh5VNdCvqFff0TMyW1+gSkStwqw=='},
        {'Description': 'JERANTUT', 'Id': '68700', 'TrainServices': ['Intercity'],
         'StationData': 'iA8g6XdN44AMy8gy/6z70WN/1bqxxvc46lklaNqy/65GA236BC0Qn9PcelbTTvGKMvED5nsEkg/+adRFox6ptVPheAmqDIzCFkOO5OgfoAJoRDNhISerbCFI3rA8fdqbB7lHZjY9ys3Jei9qpvd9xg=='},
        {'Description': 'KEMAYAN', 'Id': '63700', 'TrainServices': ['Intercity'],
         'StationData': 'y5UWFLKhPkO15Mswa2LxvhkoElps73kAlpkQhG9S7IcAevhbOMcdGPuvuZhub/gEpnPVw/HlV2BGfFz8DIerayJ9IX2hy2Wt/T7MCb7LFl4dqMi9uBnxltXV8HjIRZTpmWNqmHPRZF7u2/tMMsrGWg=='},
        {'Description': 'KG BERKAM', 'Id': '72400', 'TrainServices': ['Intercity'],
         'StationData': '+kX9+ws8LQAGlN/vgSWsuq5MkxQvuybtcwyt5TcIPOJF6R0QLFc6a0kZEzxXWzK7wllaNQjON6d3AV/n8kYYg8b6Av/hHLtWFEQmF3YpwE7LQ39k08cimvDwOqzgBNn61UGWAYJF3cBsJIMYWalcKA=='},
        {'Description': 'KRAMBIT', 'Id': '70200', 'TrainServices': ['Intercity'],
         'StationData': 'A0wkU5ydRdBG1/VjkBpv5tih+6gT0GKrmG1arSoXTSiZdQBCvOAL5bOvRjFiYfQT6Nm8o19zVPcuiwnz96mFlxugMB6BIr+rNPJTGlSePTXJPpNLzidTAb21WYllUqnDTS+XFCJ1JmvoFON3pbdf7A=='},
        {'Description': 'KUALA KRAU', 'Id': '67400', 'TrainServices': ['Intercity'],
         'StationData': 'WYg9FPx5TNN1p437LGYnwbIYwf0Rx+3lxYsqTgzvK610C8nKsb6mFXnUFnKr5QSg0DWn5LwNFHb6PTVUPzs2eCTEGQIvI572Y1WYPhiieUSp0iswHhPU/FPph5J+DbasD6MQAvWJewfVWVi4K4mrtw=='},
        {'Description': 'KUALA LIPIS', 'Id': '71300', 'TrainServices': ['Intercity'],
         'StationData': 'HDx72/o+zq0bPXCTmIijooSfhA8SKVGI0LCXGPN9NQr2JP4V+hDCTNCG7nlGyLpgWYgUNCgO5g477UeJ3M54h4HfhuNeUJUhASxoWHOmyXy+dEH5e/A/70wpXWLctnSJ4PCodsORa4fjD6QL0o0J3A=='},
        {'Description': 'MELA', 'Id': '69600', 'TrainServices': ['Intercity'],
         'StationData': 'F2hcxfr3UoUyYXQCbdkAoIt66heZWS+GU4fcpoWL6Ydo9KGhKwMWv5grqzaiFX4rbrJwcGqYVDxzwAJD3yt5ecI3bYSilpomgtL0cAY91DxnKELm58Jy7zc2r0GkVrj19a+pBtVINTZfrl7V2/5g+g=='},
        {'Description': 'MENGKARAK', 'Id': '64900', 'TrainServices': ['Intercity'],
         'StationData': 'zrydexDsTvkEPSbAn3XRwE3beytdnBClT9azgELO/PQclhUER8lcXLIGseFKL2oGk5ySxocgS3jPNXiDT/rYFUbMo9hD+U0QXs/Hc6ZcOCoguazmVmy60YxmD72S4ey2hmGr4tNjvnsmHDhm1gEpLA=='},
        {'Description': 'MENTAKAB', 'Id': '66100', 'TrainServices': ['Intercity'],
         'StationData': '9cqt3cXM9ZsWHRHx7yGUE4SamKVfJCrWuRzhGqq3qxGUePPM7BcCjuqaqWNaRUAt0dKjRweCeotanEfgY1l7RBP2bjUHd62GXE+CLyqaviK4f3zMUlMnk+XYj+AAQ9c+veg/V9VmFN9hNEwfR07SSw=='},
        {'Description': 'MENTARA BARU', 'Id': '75000', 'TrainServices': ['Intercity'],
         'StationData': 'AfYIsf/H7mVuUZmwgZhdvI7PX+uMsXY4ngYn+LRICQlRwYej8ZIbLUERxJy3cUMj+kTwR8QQNhOmrg1p3MNBvKGvuXhtvY3PX0tHno5NlpHnMvFjDs3hmrT601obcDqxAx6vVShMKFZvtzqrjPxVLg=='},
        {'Description': 'MERAPOH', 'Id': '74800', 'TrainServices': ['Intercity'],
         'StationData': 'JBRpdJyzgyHBP+eqwDSWr1Fhsqk72x2Bzw9YDqP7U9NOVr/ydAAgjnRFIWwsmlncMfhJ/a4iQSyPesFobAav12MGSWa+3IYurvM9Q/7fmEHOAvoNscHjmqMUHrQkWSWKsgsQUQH0O1M/B4/PpmHW6A=='},
        {'Description': 'PADANG TUNGKU', 'Id': '71800', 'TrainServices': ['Intercity'],
         'StationData': 'guceLSVmHVNWG5fk+Y1n6bWt07P/Qi4TpTTpUY5Gvww2bP7h+jtmed6F7hlZl5AnynMDcJK2H33E4cgT11nVLizBeHunTeVy0m7pqthcK79ZIJhSD74ozqPJ7sbBkoCiwQjKrpa8DKdsP2bgmYSiFw=='},
        {'Description': 'SUNGAI TEMAU', 'Id': '73500', 'TrainServices': ['Intercity'],
         'StationData': 'qdCKeFWutWxLKMrE4TZzT2MkhlZz8FGmpQwq+L5r7B2fE4lgn2hSL7LI7KCA58UYuXsiEWyIZIR9+gDx/WFrLb9aAR019S9wPL+zJWaPMv2aRWuY/R4uhuatP0mCq0xMmsTq6PJ4F5KK25AIYF/DoQ=='},
        {'Description': 'TELUK GUNUNG', 'Id': '74500', 'TrainServices': ['Intercity'],
         'StationData': 'Iw6+7gHsX4K5pSfZX8nYeuvdyfN4ZRGa/UmBwvbxMaMhdVbNph/FeNzroMnAoSsOkzOMQ5M8y+upKXaA9OFPvc5b0+yp4Xya961D8oyZQxmBWX3urbQ7fXvwJfcuerxTnK5tVsID805bR6aPouo29w=='},
        {'Description': 'TRIANG', 'Id': '64400', 'TrainServices': ['Intercity'],
         'StationData': 'vwJ3GiXWe4+Q8BpO3/IAYhwoQEQ/kDE1bhL2bizg6op+aacq1TCYoMGTzGKDNQvKtQf+9SUFcerFnI8IaYd8SL9/Kwc12l5F2bjtEM++2qnM36jmfjGg6mGEBJUzZ9E6M9gNLlb+Qx5Yqxpvd6OCUg=='}]},
    {'State': 'Perak', 'Stations': [{'Description': 'BAGAN SERAI', 'Id': '2600', 'TrainServices': ['ETS'],
                                     'StationData': 'UO83hCLi+Ot4I+LESJU6yLQgKMjMUO+NnUe1sNeDtbhvdMZsxFr5ppn0XwK0CUox0b9/K4p1xstrqa4c9wv4/OEk68nlMe0h4fDilVSc2jZluxMsdyF8mZt0DwvJc9DyG2251gynETmPpxQX9UlISQ=='},
                                    {'Description': 'BATU GAJAH', 'Id': '9700',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'fC+oE3tfCurO+xN8AqJjAF4ymDitE4NDV1rI/BoxdWnb+kYaSmZxZcTQ9fTRlsBXr9Wr/yvWCulvfowl6eGf665nciDyCb0a0hyBayRX8yKvDZ238dD1aO3SXXX1fSGzWA7MDnnMUnV9MKZX3Zw4TiASRppEErYT1OyWoVBLX+o='},
                                    {'Description': 'BEHRANG', 'Id': '14600', 'TrainServices': ['ETS'],
                                     'StationData': 'Pbv/vOZCOQl6zKICSL8CY1aHVt924gcH7O68ivZCvbJHZ5PdiHBbg5X2XqjkaNJzExg3q1AbdzcazBE1u+M/l1qh/f/OGanmXM5y602pD1A6mWm+l9IC48APTOZ5HOBh+Ob6CEM0zJMegwauYz6XXA=='},
                                    {'Description': 'IPOH', 'Id': '9000',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'N4KHTVIPWNI1d1WHtLtJbTU69F3fEH0AjM65Y5VZ0b4sDPGxSq+UCr+vi+SAdb7a3HKtm9sm1+iECogb1pWdw63PheeARtYXWc//Ofc1D82IMbUtd/GNEzKxeizMNpxaq8LgoFOqQXrDWHVO6AtgvLg1T5cbf67RxSWSwhpO+rg='},
                                    {'Description': 'KAMPAR', 'Id': '10900',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'NWwqTi2BLoIFv74izjUEiIaVnsE11tg+Wfifx89kHAyJiOu8ceyvp7WnwVmN89A5+WOfCpbGmQiwhNcBXcBFJc1rT0qtL5NjJG6u6Ucke8k/1EIhSXob+6tne2G2HMrPsbZiY+T8h2tvgElwcQNSJtnYy2tmAHe5w6yVICWct88='},
                                    {'Description': 'KUALA KANGSAR', 'Id': '6300',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'Ueu62PpchaATPZlLzxW9v1XlP6liOj4WNsx1UBW2gXBRQsMXp1vJ5gDZqnrIUzOFs8dgVrLbr4RUgEzQ2rPr98ZtHNU21ORJnAipPH4GijPdW6lfmu2vDWqkBsMLEvKZho0D16pwhN62F5kCOxBkMVJPQVcbOb3Qp9uNDTywO0Q='},
                                    {'Description': 'PADANG RENGAS', 'Id': '5700',
                                     'TrainServices': ['ETS'],
                                     'StationData': '7XBNSKMms0SZtd1p13ch9+5ytVw/ha1YJEHixldISKZwXrGlg5gbudR00X2I6SGb/HujOnF0uofuF8qI3eEARAVbT+7+5ARTLcTYzB79Aqjc1nwQFUkfHCDw2Y+tr39ur6q33yFIvlO05Zi+G1WZyg=='},
                                    {'Description': 'PARIT BUNTAR', 'Id': '1900', 'TrainServices': ['ETS'],
                                     'StationData': 'codZgCk3CkobvtWpQmroAjmpnwiU9PVq0OCsV/ov+35O6EAUoLOKa0VXhyvfNovPRU3GoRijv6JKvW8CKVdbD9ms8PwxHDknGX4woKMvKNmpMro9KYx+Zr05ZlwJ3MfXeh9oTdPBFGOBMLcpbUJhnA=='},
                                    {'Description': 'SLIM RIVER', 'Id': '14100', 'TrainServices': ['ETS'],
                                     'StationData': 'KwLme1zWCdPGv8fehSWEoyNfP7PvbAeIlAFHzKM73QGgxUzLls7SbJoMaIQy0JI5liRDvVqZyZIeXob57hubEC9DI19wziVFpRz/FkNF43PRx2hQfofSzzVu4j4sn3ByeLIpWbwhI0QkqRVzd/UAmQ=='},
                                    {'Description': 'SUNGAI SIPUT', 'Id': '7300',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'yew2VLVKiVILnLx5tmpcZlcNf3QjmsxC077OkpZuxl9v9XDTM6EiaoWkru/hi5tIjfc0vAvpkcPgNoWfqJg43JojPuvpCw69iUYa3me88wX6RePWOg+ljk9Q4eWjeU05WqrJKImSqzPYf2x9HeqhlYDaG//2MYpFe/6pLtwc9q0='},
                                    {'Description': 'SUNGKAI', 'Id': '12900', 'TrainServices': ['ETS'],
                                     'StationData': 'wI+mG2L57eEy6AL9Wk8II+HjeBB1hNLaX4HwBUJfZr0cPwn2IAcG5MQPt8bOy4y6zQsYXo8Kr1auEhPJyatMbyp5NZ1iAiOfgRvNHct7C3eKO/E6q+VUqGPE0cU/Zjg1E6Vz3rvXSmOGOI4q+7IouA=='},
                                    {'Description': 'TAIPING', 'Id': '4700',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'JDOIU937VQZ0oTRWrj5F2WT+WpsSn0aHLP/MNO3HWuT9LS39M5whznO7+FJUPyYF60+8oEIguItF6Hvjj0BRynReCqroTPFY4+LnkNQ+uiOz7j6f35Omnr0BmmnnATHnVFLdKIiOPbTfMAvYtmOH4blbKGbe+FCcTHY+tCsTTbE='},
                                    {'Description': 'TANJONG MALIM', 'Id': '15200',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'leBBRQ5/5va/jiC9rQ7+qVwPnRoQX1s1P1ZY57ovfU6AnYbrJKNuB5DF5yQFMIf0ybtKBTzwwWqfLv3/0Mph3/O+6/iyJBzecjUljPnCgIRG4K6il4Mwpw5eSItWT5TuaBNt0cIUr7VVmykTgn7KhXpZ6jY5xgoqsOpZEfpTEws='},
                                    {'Description': 'TAPAH ROAD', 'Id': '11600', 'TrainServices': ['ETS'],
                                     'StationData': 'R+96yTNB8s3oxfKvZY2otpgktpyXqTXSxk9uHCscH/d0b6e0jB8TleiA0WVLxzqxwmTnNwNGjC/F0ep0+UM97Lk/sHQsTd3aV/9pIGn8+uYwPyo8WODA4NMBalncmcgIrGRY6QlgRYhS+SaRciWwgQ=='}]},
    {'State': 'Negeri Sembilan', 'Stations': [
        {'Description': 'BAHAU', 'Id': '61800', 'TrainServices': ['Intercity'],
         'StationData': 'DMdF9msJG131xMUuUftozxvgUQdURJUeZczTYHhyE+kVpzLIqmNKQ23xWYug6EszS7IjlKL8e14eczBurF4MBOJpeWXAjjeXZxGgR5cr5tW8y411DDoGLZixcfCnQy1BwFnT68XtjEs3bUwGF19jgw=='},
        {'Description': 'GEMAS', 'Id': '27800', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': 'JuxUMJMPWEXHIN+59A4ow/huYMG3NGlRVGrCCxj5p5o5jH1dACi8dYGgdBwEprzcz6af8ig+PfIdrSXqY5HybPu4cUX1uHqzUodykTXwX4bwzCzBgSo2qO9Q3qmVljVBmsS/EbyvC0kwwXOugf6rM7XXcofNQ7of9GxwF36uQgQ='},
        {'Description': 'NILAI', 'Id': '21500', 'TrainServices': ['Intercity'],
         'StationData': 'QyA9RCnEH5opEnhMjaNsY0aw/VEERptUv/B81xO6o4tF/F74e2k0jWGb17aK608VTZhH2rhA4RZbCK8uF2sNSmJo36sgnYfRUZtEIVx6R31dKzKhTZ0/D2l+nweWzvoq4RPd75EREdSY02YIWNrnTA=='},
        {'Description': 'SEREMBAN', 'Id': '22700', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': 'SjMV85rnr/ZTNWsIny02ni3yeva6GltYRsS9bSOZ0AXk5g3kAk2/o6spFGQrQvSmWszPL4J4ebNS86vTqBH50HFr2J0pYOtoIwRyXybNaVnz0V7cmrZDKZ+F8L0i0XJgNMLr9fnWwboJ/wT1GTPy26FHMiNxF7xVhVVGxN8p3z4='}]},
    {'State': 'Selangor', 'Stations': [
        {'Description': 'BATANG KALI', 'Id': '16500', 'TrainServices': ['ETS'],
         'StationData': '4ydet83YfyZ2kU20q3MjpJz+f0iFt3X8OiVc9V/JHCiWmpaCNLG6N5y5w45iNhKh09DSLTZ+K2WR7VtsgrTKqlRErDpVHu4k3164mCDZMSmG/qI0PTg4hJBcSwaJVBUwQvujgIWuzbGhx77DmoY8Tg=='},
        {'Description': 'KAJANG', 'Id': '20400', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': 'iBr9S6ft7FuPWgwXciSZyQs+Z4EIsOODUOHzLS+1MPKzG3GtpN93l6lBXSoEwyJZsi6rGsJj9Tjlxm+/BtdA90+KkqCR1+eYp5vHb7zosyUC7pqLFPJccZyXeFOX9gA6/fnu+6neLzagUSqlSDeevXzgRDGacGGMuqnrQL/EUcM='},
        {'Description': 'KLIA T1', 'Id': 'KUL', 'TrainServices': ['ERL'],
         'StationData': 'v1PalDrpHo+Iku8YL8+0lMZyh5rYgshxD1qEvnKlDTiuXDYiEbuTxONCPFq4tc6m6MqoXX46BmUvRDioQ+EtSxwLMfyHI4N/IZvNp0MIH+lbJi1ubKQ2hy9uWXCF9aPpT508Ku+Az7eGVxXBkj9WKw=='},
        {'Description': 'KLIA T2', 'Id': 'KL2', 'TrainServices': ['ERL'],
         'StationData': 'Ts3UjyQcPPSmwFH5Ngl/20GV90fg5j/mUL5byfKsR+E9IJWD3vy7Fo+fz/MoX/CHJgBmAxPznZt+0EvtKTVmHQQWs0OwHJGegUziAfKjWataSM+RInRRhIHGj1OVbo2Ju8P8mJ4uh3KoaW5zpMdx8Q=='},
        {'Description': 'KUALA KUBU BHARU', 'Id': '16100', 'TrainServices': ['ETS'],
         'StationData': 'a/uydKgpmFdGYIEk1lIVORcwFtmLFYdctThFha+PlXd/WTxt4b0+MBh/jnweBudit40OUGzsLeqxXU2RiRCeJ+yWXB+f4ph9Ay4RoVRLeMtA6e+6ImNJ8CsBg7atJ51ayecAXYURfgFgLR1La2Cowg=='},
        {'Description': 'PUTRAJAYA & CYBERJAYA', 'Id': 'PCS', 'TrainServices': ['ERL'],
         'StationData': 'cNf5fJXn8fRiUwOt2659Wyyxr88ddJC24mMzw7vcZ9qg0xrD+O+QYUwQGUKiQksEYIvRadxBh1MYxcpd3nfZZslK9t+/LqSpsrFTbvySFSfstzrS0XIMzUCan1D7XWDK1cEeO3vZ8RpZiebLtKXfHLHK6gSWUqsazsBvXVKj15k='},
        {'Description': 'RAWANG', 'Id': '17800', 'TrainServices': ['ETS'],
         'StationData': '/4wyX8/jcFJr7s6K5BcbeF6L+eRP6X1ylPOVK+zI6n59gpMREqB4ADjV9QjcbdPjDx95dge+Lo3d6z7JAnMVfJfS0dH3XB9rx0No3+m4qm2AEhoRa0G94dSmOUDpMTvOvMlmWqqArCb44uTeH7lmyg=='},
        {'Description': 'SALAK TINGGI', 'Id': 'STS', 'TrainServices': ['ERL'],
         'StationData': 'Kd3rLr60LjcCXtvNCNWDT4xn1bTmaRY6tpBJIJbDoYswwFNQv6nNteLBsoM+qnodToeQZBVm1XpeP5SEvhePReN4s+c4od3vZOtODsoE6/niHBzvOQhY0NL+qMU2tymms7FnC6PNdmoSgnJqu5hbdA=='},
        {'Description': 'SUNGAI BULOH', 'Id': '18500', 'TrainServices': ['ETS'],
         'StationData': '8zoxo0FqpD+z17NLoqfxDG7yW41WesUxleAnGp+oiO0NRpbJqZTWFTD+couQrbrrieuPGebCcwoyyXTVY2kHicgk4HXrU4yeyhro5vqC1WpDmk9/2Hb+A12IMGvBYHXan0lkAOic0GAJ4GH0OqxdMw=='}]},
    {'State': 'Melaka', 'Stations': [
        {'Description': 'BATANG MELAKA', 'Id': '26400', 'TrainServices': ['ETS'],
         'StationData': 'DpoPmY4B9iKQlwZWXZvBfAceVF1PGqB3Yt2JqHDasMEPo9yK8C0xS/724T0LQR1hxNNOXjgVztH6NSxJpSkYyEJSLMjf0PXI7iLVA+78JkxxfLikxhX21KP282T5nog3eotqxU7tNbUzeC2Jd6Q4bQ=='},
        {'Description': 'PULAU SEBANG/TAMPIN', 'Id': '25100', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': 'xPSxNBR9IRqxB21iWfYi028y8LlE+P691yrLQE4dqw80a7Ess5y5ljB9c9YTpfuYhcG5d4hNm+XQ32G35NfUs7Gt6RSSAvLyqtIuOtx5z/Y67Gz8N28cQHwNmX+kYRFm5gA1ZirKieuM3H0+sFw03eHiO3gdRsQeYge74pCmH+arLn11tyutSRlk0dWcvOwr'}]},
    {'State': 'WP Kuala Lumpur', 'Stations': [
        {'Description': 'BDR TASEK SELATAN', 'Id': '19600', 'TrainServices': ['ETS', 'Intercity', 'ERL'],
         'StationData': '9TbT7Xw90g00SBLFHi4GSlR2dIsqzI+jnYqi1Uq20A/lYMDwrsA4LfIgVw/UfzpVYnJ0TrrEOvHx8DraPpnSTVu9/L76U0n1XnDwHZ4MWYl4vG8qOSn6pRsTmqjKTaLtBK9wtiLpFN3BGiGQMEnXsyF6FJl/vtLwlFBor1UffngsF8HkJ2ZpKzWyJkg8A0/loB+QDoP+lVL4XlBbUl7Nmw=='},
        {'Description': 'KEPONG SENTRAL', 'Id': '18400', 'TrainServices': ['ETS'],
         'StationData': 'mQrc2lJdrJcHcLJUNjoEoS5x6GvHzBgsWKqQ60q8Y6t6yV9q8bnWwCGD9YNVQ7x24UZQlNsipQjtxHEIJg2ho+s0wdFrBShc8LC2HRS5sfV0orNUAvZXDuBcWwYs13SO1eV7v5ekoJulMicslJAQ2Q=='},
        {'Description': 'KL SENTRAL', 'Id': '19100', 'TrainServices': ['ETS', 'Intercity', 'ERL'],
         'StationData': 'qd0jssEp+dY775lt7fYcwCB7UQp40B87x+Nqwx4fVb44EdvfjREj00866qYYUTH4/Qfj6ruQZ5FC5JvpDs8AL3MqbZn8gzXvZv1FTM9iE2qya1fWteGoE4QhUTfLbSaoOiYyqlUFmJOXZ6dPPfQ67qxE9509JV9YmPaaThabvuH/LkI1SqaeY8/7FXHdO72WzA0IHGRJvng6qtceVmWH+g=='},
        {'Description': 'KUALA LUMPUR', 'Id': '19000', 'TrainServices': ['ETS'],
         'StationData': '5djVFpelRLc7G0o6cw2rqmEngm9v0Sc5tsqQFmZwQJTsrpl2cOlnAPcN5jVfyB64x961C13YvbEgWcU/7pCkmp3Q6+n4NMebp/GGbylels+e0F+oVotcyJUDelJJL8X00Zfe4VvhjcVFxiPrRsh7Tg=='}]},
    {'State': 'Johor', 'Stations': [{'Description': 'BEKOK', 'Id': '31300', 'TrainServices': ['Intercity'],
                                     'StationData': 'v6hhLgKcJC1ZOrMnDTGwJuAJVSzXejyV9lum7aEHU+g8Td5r1uCYbPSP48sP+7Jyl0/XKkF2gVN70UpuwrRe8TFmbWSXR7EmM9DGYWMW0RIGwlxF8ma9kQuz7C/rcgeM+LN6r69dVdU/b8ef4/dyPw=='},
                                    {'Description': 'JB SENTRAL', 'Id': '37500',
                                     'TrainServices': ['Intercity'],
                                     'StationData': '8Gk28XfdAPuHHsMTxKwlNJVhNT+zMuXiANgQegSyoaXQQtetNfBLMXup7HJuCpRYHrzaouoVASkDG3e+ua9kyBvNIBHHZfRss9vFAxW9prr72j4Dcrf5iSkpizh4A3uvtmE5GhTUho27bAivTmaZFA=='},
                                    {'Description': 'KEMPAS BARU', 'Id': '36900',
                                     'TrainServices': ['Intercity'],
                                     'StationData': 'N7T1n50rWSM6h9eQmyB+2VUKYpvVDSuFkBKHWwbRfZ6+BfMXnkM7k5a2kHWNkK1qQMf869E0myLk6uIObJmz8mKMVcscmHFdSQnq1F8nv72Fbyjasf1yZdz+D91Vux1YVNUmxvb0lZ0xxELKY+oQ7A=='},
                                    {'Description': 'KLUANG', 'Id': '33200',
                                     'TrainServices': ['Intercity'],
                                     'StationData': 'j7Wot4yRBsgafbFpy7sK1jQpi2xz5QUEPIvZggVBdNtwn60GBTm/r0JPdCyOCrh2EFcgCN3nxJxWOkps/TuPj9N20kAdSDkCr8jOfZYSRH/d0ojdPuOmCWODF2iCIShaGHaTj4YznVkDZHcqiOEX0A=='},
                                    {'Description': 'KULAI', 'Id': '36000', 'TrainServices': ['Intercity'],
                                     'StationData': 'Bewtz+8/XYePYbM/TUx2k5bnkRlEjaNuSddguW0dj3puZuvRmGJv0Qca1UOy4+OPnwf5kDZ0AVcRJbsj13WvweXYj3iR3P72niEDhPKHN8ek92nLOQYAIQWZQj0TphZ21UztBuCyOHa+7zmls1tATQ=='},
                                    {'Description': 'LABIS', 'Id': '30500', 'TrainServices': ['Intercity'],
                                     'StationData': 'LWnManbD+I12r25AbhLtHueympTxJZjVH+aRJK5EW+JveBkkn8swS254Uk3WDmbFaarWSNi2WRqmboBNvCvegsxnBZzfoC2zc6L/3qxdbsTsuA1F4aM55AC4Y5WzSQfL8mbqgOQwvxIfzy0UKhs7NA=='},
                                    {'Description': 'LAYANG LAYANG', 'Id': '34800',
                                     'TrainServices': ['Intercity'],
                                     'StationData': 'VvJXG02+W5Jdd4qi/mIDRbvlIbTebWAi6OeuxttP7atZix6dBdLdeQZlisAKqrBUhlyssY/a9XgtXzmf3NQfRJNVkJxsZ9cFZIYXcsCXzygsHcGEj/0TjwPuHXNFVgFaXbcu8T+m5pc4y5KWuJNflA=='},
                                    {'Description': 'PALOH', 'Id': '32100', 'TrainServices': ['Intercity'],
                                     'StationData': '53pOECPtVKKEMR9TdqCiEaTaN4kZqC+YGp5rrbkUwBIYx1O4rrPEqFbcJsfm+iQ/qrs3hdcfaAsTRTB16yqnd87JZ7JiREycJsHX67dVbYGVmKAb5M12y64p1yhZlTQE1MXgVznyB3OOJfixVzVtEg=='},
                                    {'Description': 'RENGAM', 'Id': '34200',
                                     'TrainServices': ['Intercity'],
                                     'StationData': 'F/rIRi+AViqk4uqavzZe419WWXhA0bsDAyGE4DHEb2dlZMw3iFk6PuhZWYQJvgZxjV+Em7+J2TVNr/YacuZz/UTZlLRVx1Z5C4PXIPFKNRDCw7isahGcyZZUbBvn1clm8XJCVND6UGIkwr4u/3+CQg=='},
                                    {'Description': 'SEGAMAT', 'Id': '29100',
                                     'TrainServices': ['ETS', 'Intercity'],
                                     'StationData': 'JImrQc8Bg6kKQ5hnQnf2I/8Wb/wyzhMu3rYuQndo/yd38uF2kOQsjFvxxZ2jQBJ+wzbUAoULsFaVEc2ZZFCbia3N6i6SLPnjcaFItyB2Y1pB4GKMB5PyaUsijL+07jti6E0jVJVowo79sTyRt76eDcbRv7oIL7WJrAyy4Z4vYIE='}]},
    {'State': 'Kelantan', 'Stations': [
        {'Description': 'BERTAM', 'Id': '77900', 'TrainServices': ['Intercity'],
         'StationData': 'YQXlMttJH9cQFppgUGykkcQ5UWJSPjYbOQFVoZpwCqLlQKiDizkqtIWVnGcQophHh3H49l/vxm0u/8ymr6EF7dXdsSHIJ72NMs0lyAMKR5ER/LzqHa+7yITRoryFxHNoRFEaAoKR3YAUdqcvxoozjg=='},
        {'Description': 'BERTAM BARU', 'Id': '77800', 'TrainServices': ['Intercity'],
         'StationData': 'VJ55wamqOD5OGjUEkvYoSBZ065BaEyBI5a/BYjpxyBgVwx9mbeYcyDVaFcPNT0xzER32tg/jwedE21cmKu8v+QoZaU0RxN2EJhVJgptuzlwaDbUn5ZU5FYxY6QJKyc6oBxh9X7EmkbdcMIkKtJyU9A=='},
        {'Description': 'BUKIT ABU', 'Id': '80000', 'TrainServices': ['Intercity'],
         'StationData': 'R8iP8mXTrGctaKB9PFwASgUz4CfnaVmgcUvi8Ikn/lFzWoBe88EBflhU5zyIyYn0HqJwTODRtWwGou6WDB97ahpmsPli4iTgfh9zLb6uPZv/o2q2M8pl1KhLjwxDBeY7lvfWwY4kdDTXjFyHCyEPsA=='},
        {'Description': 'BUKIT PANAU', 'Id': '84200', 'TrainServices': ['Intercity'],
         'StationData': '9Y39ojmYMe9MbbKzBCTivgyPzrT3yWmzN8AgDG6Z9P/6kbFQC3ZBbv0dh0f7y0vwl9tqrD1IruMhO52wvVGTKczbd8u0lv89Nl/TmGKq29yTSpv2J0qymi0BJnkOebaHkksG3+CnyNNX/OwRbkM5HQ=='},
        {'Description': 'BUNUT SUSU', 'Id': '85500', 'TrainServices': ['Intercity'],
         'StationData': 'im69sm7QzCDOOfeGTHqY9B8E4H6WByKgx8OpbSAEZ7VsSQ6EH6fIADO1AKbTG2tGi6l7XDNSl0qfwA+7aK2XINdwz9pF9ytI0rFLF+w31h2GmfL8oCl4TI/4BROUclGfbuVNdywuBJVb2q74UQrX+g=='},
        {'Description': 'CHICHA TINGGI', 'Id': '84800', 'TrainServices': ['Intercity'],
         'StationData': 'LGHYUf242S7y0mJ6DxTMjjPaUdOCSEncOuZiDMzi4Pi6J3HDQUG20NOb5tUfebQuwT7R2lUOpOQXHtLyzkJ8+g/jUOOZ4EQKNC3tSN0seocctjXs37XfKGEnNa0im/DUPw+Z+lw9LO7569aE7R5wIg=='},
        {'Description': 'DABONG', 'Id': '79300', 'TrainServices': ['Intercity'],
         'StationData': 'HThq/7pJHEX2Vde4+0i/erAo2k+WDZW+sezHJaNhDfsTUM4GrclF7sA+fT6DWnxInK41tWBPnSmTVmiu+m26c/8U4+zGBT2XRgPeMkiMskzSBX9/tL8B/DxWI37ej1fuib3noxy2fVxVrZ6ZZWxW8g=='},
        {'Description': 'GUA MUSANG', 'Id': '76000', 'TrainServices': ['Intercity'],
         'StationData': 'VMt3E78Pjw9IeF/Hk5P1LNRyDUhi8S92A8BZhYh7naFojGBeng42PxleJxZH7nqbnvw69tly2LR3yzSHG9WtuX01hSUevXjWT8PuZQs2qRTX0asFUHzSPkp4ODMQ29DDCovaF5rS54x6ibRiCKH1zg=='},
        {'Description': 'JEREK BARU', 'Id': '78100', 'TrainServices': ['Intercity'],
         'StationData': 'q6GT5glg64HMkCnd5OYQJH6SN9yknCNjflrBD3aKk3kCFO6dYnAbRtB2QSZEOPmr0YMdYlHjkSbakivgc1eNzJ3SftdkKu7LhgBKBtCCu0614VTR3/ksq3h/EAUHBY+D/Sl71xA4CP8rHMuhqIkaGQ=='},
        {'Description': 'KEMUBU', 'Id': '78900', 'TrainServices': ['Intercity'],
         'StationData': 'IW5bQOodDlUoJl6CMrGq0VNnswnkMoeM9LwdSD5TGRzH25hLc8ozjsXbQowJre8wcQGhgo1k8kG10vBUN6DkkR3XQFglYbMDpAA8eF9BjS7S4GY0sYWuUjgJthZodmxhMjaKuX3A6tHDix80gW3JOw=='},
        {'Description': 'KG BARU BUKIT ABU', 'Id': '80300', 'TrainServices': ['Intercity'],
         'StationData': 'P0BXl3PSOq8CpNCeHbK/MwCx9eNqgPBTNVb2EiHIkit4p2L1uzCRP3jVEE4lJZ/SVBTBPxWKYol72yGid9CmJ8Ljk6nd4Sl5oQvWGlnrdqbxNUNRkQBdpTjjCjw5lj4xJk7ECbpDeXygVBqpoQolg00bSTZCi1UhUffWgoraXPU='},
        {'Description': 'KG KOK PASIR', 'Id': '86000', 'TrainServices': ['Intercity'],
         'StationData': 'K15J0APym2yRlCwkKT+IWtQeosHkaIvfZx/7mb+t22dyUcCF+bO8uYzv3eDaWQ//89gqhnj2UmTArv4O7QYii8KpOhprxPyaRQMZYvH4rgJIbajOnnfOuoK0PynrE9QmkqzDGGhYq9Fg61jQLxUR0w=='},
        {'Description': 'KG. SIRIAN', 'Id': '77000', 'TrainServices': ['Intercity'],
         'StationData': 'aAzbDBv9Q0eOJRUHg4JGitc72Bz2pPZwPJMDdO/LnY3+lq/iYg+FFh0EQk9sMEkhaPNmj5l3P8YgwI7rHoIBS6vKSDGHkMBFA7mQrtx03MDDPCYniR6BzNju15UgYi+tB5eGjkk3u4ZbSAFXLWwkQQ=='},
        {'Description': 'KRAI', 'Id': '82100', 'TrainServices': ['Intercity'],
         'StationData': 'qzB+x41enNGgfD3sx1KSssv7mkB0EpUmo1VHwNPsX4atg67+yxQfdjTvK7DT0Hxi71zCHwLx7tRmfkkyV7ggwi/hy4nNByLmwW7H4kWUtKst/S3f5SAt+qRsv3TCJsrH5FGHEyMc0sWVSI3SHEB3fQ=='},
        {'Description': 'KUALA GRIS', 'Id': '79800', 'TrainServices': ['Intercity'],
         'StationData': 'qDWv7ES3tEZRvVMWfBHHSm4HDMhN1hOC2N1pVB3z+5Asb0yTgPcfUmPWSFpwPbxhkYhH6uWq4JOaf4lOGvsPFy+tVXHbKo3L8vhyoJofZKYPh6n9d0T4eLn8Facexp4inzCSm25IXziphMkZuTv84A=='},
        {'Description': 'LIMAU KASTURI', 'Id': '77400', 'TrainServices': ['Intercity'],
         'StationData': 'E4OxCtyFJ6CKjb7czdQXvLEly74ykfNLbRnfFs1+3MxaR3o6xBok4Sxyov7yZvulDqrodf6XlMGLFT9Ux1ZojfsfgNN6Pp+NgWDdlVkKNETFKwLtgtOU4hI2EjEIDX1hQx9l9gOsM3w0xsiXo/lU1Q=='},
        {'Description': 'MANEK URAI', 'Id': '81200', 'TrainServices': ['Intercity'],
         'StationData': 'qBJQJ/0j11n0dIz+Bjsf2mZy6VUIKax4eJ2O3RNJtLi7oZNzvazUg1ikDKme0DrYaR1l8W/An4Imw71hgfREXUbxwRF7/KxTVcI0fWrV3UxsncT067hEQwlYjRZbD71aLpjGp34FJEnHhqvnYZuhVg=='},
        {'Description': 'PAHI', 'Id': '81700', 'TrainServices': ['Intercity'],
         'StationData': 'jRW2NYP+mvLopMH9vHj0hY6/0vd8v68ZwDTJnxKyA5vUPx58uVBGN1qio7l34QcjQcZ66GIbH3zIbbcRAiJ7o6oP1PeD220Ek8yExxpXIblMi9xu9FbePq6YTUUfeAHWx9ieWl44v0nIFGiWSa1ehQ=='},
        {'Description': 'PAN MALAYAN', 'Id': '76600', 'TrainServices': ['Intercity'],
         'StationData': 'w4wmr3g/oMO2VHNKM5xEqkk6RqYppFCLyPaOgvYa7YJn/en4/RdOjf4N0ZwK55kIIwRnQWy7DKef/3O3ULlFMzr5yZnq0qP6kbs50FjnArlhRupqvNESalgwTKyxLKrBG93248gOSPk1JBgAfuZp1w=='},
        {'Description': 'PASIR MAS', 'Id': '85100', 'TrainServices': ['Intercity'],
         'StationData': 'jK88eEFuJccmkCquShIlHLVh8dxte0he00FLv7z5wrIv1rAGRCg5H7WnfEtBfW5Hy/G76COtYaJ6tSYegzwv7eJnGkn0VbedA9isEgfS0n5qEiq+n+3NAf0QnAR58Fgk+PgH+Z5cZ8z03UXsOE1mQg=='},
        {'Description': 'SG MENGKUANG BARU', 'Id': '80700', 'TrainServices': ['Intercity'],
         'StationData': 'e+MXSqF9riEFC36tVnweH2vSoQ4ez3aU1OreJscNEL8QlavDAukXKTq1DdHtVWRDHpw7TQcmb9cHmwWsEeh7CLb0Pury+WyBCA3otHidwVzXhAuWtw6jRspcaWSKJozn3VaCQ/MfumwYCoppHurtSMKOQkKftDtNQjGgWCbiIIw='},
        {'Description': 'SRI BINTANG', 'Id': '78400', 'TrainServices': ['Intercity'],
         'StationData': '7tFle5VahOQPaltc4PPf85F6YDyzG7rMCBrXUfDnDH82X9JfuUhh9j8N7camS9hMgONg6jJ30sTSmjTspGcy98VZ+eUm2BUan+/htGv4bjQWGAvsQvI/WUH4JTx93o+T/gGCuQbS5htSp9yJmba7eA=='},
        {'Description': 'SRI JAYA', 'Id': '78700', 'TrainServices': ['Intercity'],
         'StationData': 'jHzbsmzgsfmi1Nep12tzYnQnuoB47oHKc2naoZsVPVMARnJTprplVkJ/o/uynHyAsxT3V0LRQH6OmxSklTeXCP9M0w6ldrGz2ocL4YAx5z8dytEbkN1m2niAErKM3j9Kx78V6/a12T/QjfgnYa9kvQ=='},
        {'Description': 'SRI MAHLIGAI', 'Id': '78500', 'TrainServices': ['Intercity'],
         'StationData': 'Ubd2JbHg4HjeK1iKT3Hz71Rpn7155xeystNVZm+mR4cGncSbIWzR7P9t0sNRYh8bk1SMBAxO/AVD7EPxjbmFGFGn4mrXe2n/apsB3T56TQ+LUnfikP3Il5koQhqawEHVPFXn1xPtoQ9W5/k42XD3mQ=='},
        {'Description': 'SUNGAI KELADI', 'Id': '84400', 'TrainServices': ['Intercity'],
         'StationData': 'TgcMrGaSIakG0JEEsV/KWKu+EP8RsZMual7barNuq9uXSz5efeSBQoFYlVPzhC24FExaSg1Ur0dszwW4hhFvErNsz+ws75xwrw4pSWIR6Z38ECRvmwFuU6wUWkFca7jKlq9Hn2mZKDEdBYYPceMupw=='},
        {'Description': 'SUNGAI NAL', 'Id': '82400', 'TrainServices': ['Intercity'],
         'StationData': 'CoqJBFBXW5QQiFJJ5OsjYaaQqBFlupK8EyYdeXsqAyOfYdS8plQLtZa6CerSBdKPoVAGmJiCroSFcK0XYIevJRGj0S8S5CoqBxXTC0U2IlqBfsD7eDh2uwey56zEbBq5T0eh3LfuCfj2ToRzVFrYbQ=='},
        {'Description': 'SUNGAI SIRIAN', 'Id': '77200', 'TrainServices': ['Intercity'],
         'StationData': 'YY1Z+A9Ulmx+w/LFGZ6KiKujoYSQ9qntH5KIMJi9bAyGWCIY6BDzqUpS0tuGjdV3GRMsk+UXUf0ZDYngLTB8MlcdrC/voH92uBfGQAl2vBPqwivAQ+1dpdynE1KqUM1RZ9liymaGxGD10Hq3z2EfdA=='},
        {'Description': 'SUNGAI TASIN', 'Id': '78300', 'TrainServices': ['Intercity'],
         'StationData': 'DAwuZZH8mNYyv4CbUdAunGOL4o1Qd22Iw2dKGRabH7DFH8YaeBM/eRiOsiL9TT2dyubvN6cPmppCZLuWKwXt6GjFpRX3BUpuf6cmM+MNZVmq2+TFFX0f+DcIm80kJs1GURfN092OGsafRj9TT1MuVw=='},
        {'Description': 'TANAH MERAH', 'Id': '83700', 'TrainServices': ['Intercity'],
         'StationData': 'JKzR5JZ3qdN15SiuLo2egNRglbgkiiDMIGVP4wQjZA+oG0Ydgau88mmpU1zrC60D05fG1WJK10tLxyGvv5WjLzykgWLAPOcPluYnknYpbLrRY7K53Z2JEkkUC5fuGOXRTJkzIaAkiHUUfFpLNEElUw=='},
        {'Description': 'TEMANGAN', 'Id': '83100', 'TrainServices': ['Intercity'],
         'StationData': 'JClsHPi7iFtQZFZs8U36i27oymLkfLvnEwupTCFtzNe8r0b8hFXPJ0CR8viDMsDjxgd8sZYKR0hSZm6QlDVBWgVLFl1053dSCugEsCRLehwQZUzpG8M4qj2p8c2i3ie4KvVZJyu0m8sRfOOqvrP7cA=='},
        {'Description': 'TO UBAN', 'Id': '84600', 'TrainServices': ['Intercity'],
         'StationData': 'IF5skvpx+yc0jfC1h8IvrzHoGqe8r3K6xh39uqkyOYK3XyoF/aDYdwRhSbUPd1/H+evtGInMs2qfKNRwQ4fY1UgkC1xLij7gSVPj6ip3/xihlmVyc4jkGjT1MvcG3qwpPJLFG0aUx6jaWy+FAwhIWA=='},
        {'Description': 'TUMPAT', 'Id': '86300', 'TrainServices': ['Intercity'],
         'StationData': 'uJQNji4D/3ZhLCgaADkrfQKaDEGNEkzj5tCbtF82iW+Pp/j9kIxFfkyHC+Eet6E4SSKBO9JdT7kGuWBV/0wXtAadfFieMM5pGHVukfACRKQEi9WguKt+5xqAJPFsnCh3G4C0f+epd6BSdgoZ/3HZ/Q=='},
        {'Description': 'ULU TEMIANG', 'Id': '80500', 'TrainServices': ['Intercity'],
         'StationData': 'CvYxLF+vhEALlQtoyfQ6YJrm4Ldq5d+rYboQ86Z67TlUsm6MMEwpjQehZio/g6t2oG8nOFt7anDkvw0E0S31rXV/pwwaQ4n2WHsM37c5IWarAG2UomwN12oiONwVOUPZg76wC2xU0FhnN5hUQ8BNTg=='},
        {'Description': 'WAKAF BHARU', 'Id': '85700', 'TrainServices': ['Intercity'],
         'StationData': 'G2CFf4uxK6GjRQWOZpNSDJubgkJW1EWifm6k/P298MnEc333mNyRDRwABgM11d2Sg7ax7Mf5L20cOBJ/gUqVwfA8g3DKG8Hz0v2z5qGC2bjLwIa9Sp8g/4RqH4cskKVUZeNvW0q03CZydkKZsY8sMg=='}]},
    {'State': 'Pulau Pinang', 'Stations': [
        {'Description': 'BUKIT MERTAJAM', 'Id': '600', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': 'TcoCKR2/gM9gOxov1KuU0gNxpv36ZGNM0xiDG8DVA8h/mtgL+Be9MTI5yckBXqv7M6GnxEIn7S2atAhV91vErGpg/grefH6hjtPD9FosGvi/ObSL3QH0chVXGhtXF0GZ9m2OXM16XTBwSXUmBLrOR50sq/lNwGtv8CmTK8G80no='},
        {'Description': 'BUTTERWORTH', 'Id': '100', 'TrainServices': ['ETS', 'Intercity'],
         'StationData': '5J1ACVI4hFLEkYkGf87uzm6h017weGta81DeoD2SARCA2FNMi05aL8345dX16EkVKs3i7ILpgm5NWQnki4zR1oFCnYeSdMue4JOlfyiWfISX9wjOtdBX2qmxCpOn517DwCiQY0vomHY7ccF3RdylWUyOu4lUvnVJm+biespDPl8='},
        {'Description': 'NIBONG TEBAL', 'Id': '1700', 'TrainServices': ['ETS'],
         'StationData': 'mKslj4HP/uhR7IDTqIrRIPw4aw/cBxK4jROFTXkuSAxwZEgn2zvKSut99hZI4V9euYoDJWqnSvImA2UJlX2Lk04SYmdSxpj1neyWuZh0mmYGFlpz3dE/gKHCWv7xr1PZ4bsgyuYATVOA8wCaxtb7xA=='},
        {'Description': 'TASEK GELUGOR', 'Id': '40500', 'TrainServices': ['ETS'],
         'StationData': 'cLw+0d7w/WPluNwnThY2uOpw2M1BuofExMLdHA7c4uW3FeJ8qL/8z49kxAO18Xi/hi29MQfAnxQ+kltkfrcd9bHrkoeaJ2GEdBgF3cgBIQ0G2zDieJoyPhkq1AsKXclc2bsi78pk3KpBiXReHEqJhA=='}]},
    {'State': 'Thailand', 'Stations': [
        {'Description': 'HAT YAI', 'Id': '91000', 'TrainServices': ['Intercity'],
         'StationData': 'rSqyWOHFxJh9+smJInn2sIGqTq2JK/1KCwwsRr3blvqVIOcLxzQzqyE2wwt+E77QiR4OW15pdmzA725otScRcRafaI4kfxDnwdcJ1Tp+PGh8X+xWLMp2BBt+nSEQnRODx/YT750vada3L00eqQyIKA=='}]}
]


# @app.route('/ktmb')
# def ktmb():
#     try:
#         if login():
#             print(
#                 get_seats(
#                     datetime(2025, 4, 18),
#                     *get_from_and_to_stations(
#                         'JB Sentral',
#                         'Bahau')
#                 )
#             )
#     except Exception as ex:
#         print(ex)
#     finally:
#         logout()


def login(debug=False):
    if debug:
        return {
            'status': True,
            'token': 'abc',
            'stations_data': debug_stations_data
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
    return {
        'status': False,
        'error': 'Login error'
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


def get_trips(trip_date, from_station, to_station, token):
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
            trips_data.append(
                {
                    'train_service': tds[0].text.strip(),
                    'departure_time': tds[1].text.strip(),
                    'arrival_time': tds[2].text.strip(),
                    'available_seats': tds[4].text.strip(),
                    'trip_data': tds[6].find('a').get('data-tripdata')
                }
            )
        # print(trips_data)

        return {
            'status': True,
            'search_data': search_data,
            'trips_data': trips_data
        }
    except Exception as e:
        print(e)

    return {
        'status': False,
        'error': 'Get trips error'
    }


def get_seats(search_data, trip_data, token):
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

        return {
            'status': True,
            'layout_data': layout_data,
            'seats_data': seats_data
        }
    except Exception as e:
        print(e)

    return {
        'status': False,
        'error': 'Get seats error'
    }


def reserve_by_price(seats_data, price, search_data, trip_data, layout_data, token):
    for seat_data in seats_data:
        if seat_data.get('CoachData').get('SeatsLeft') > 0 and price in seat_data.get('CoachData').get('Prices'):
            available_seats = seat_data.get('CoachData').get('Seats')
            for available_seat in available_seats:
                if available_seat.get('Price') == price:
                    res = reserve(search_data, trip_data, layout_data, available_seat.get('SeatData'), token)
                    if res.get('status'):
                        return res

    return {
        'status': False,
        'error': 'Reserve by price error'
    }


def reserve(search_data, trip_data, layout_data, seat_data, token):
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
        # print(booking_data)

        return {
            'status': True,
            'booking_data': booking_data
        }
    except Exception as e:
        print(e)

    return {
        'status': False,
        'error': 'Reserve error'
    }


def cancel(search_data, booking_data, token):
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

        return {
            'status': status
        }
    except Exception as e:
        print(e)

    return {
        'status': False,
        'error': 'Cancel error'
    }


def logout():
    try:
        url = 'https://online.ktmb.com.my/Account/Logout'
        session.get(url)
        print('>> Logged out successfully')
    except RequestException as e:
        print(e)


if __name__ == '__main__':
    try:
        login_res = login()
        if not login_res.get('status'):
            raise Exception(login_res.get('error'))

        _token = login_res.get('token')
        _stations_data = login_res.get('stations_data')

        trips_res = get_trips(
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
            _search_data,
            _trip_data,
            _token
        )
        if not seats_res.get('status'):
            raise Exception(seats_res.get('error'))

        _layout_data = seats_res.get('layout_data')
        _seats_data = seats_res.get('seats_data')
        print('\n'.join([str(s) for s in _seats_data]))

        reserve_res = reserve_by_price(
            _seats_data,
            int(input('Enter price of ticket to reserve: ')),
            _search_data,
            _trip_data,
            _layout_data,
            _token
        )
        if not reserve_res.get('status'):
            raise Exception(reserve_res.get('error'))

        _booking_data = reserve_res.get('booking_data')

        print('>> Reserved successfully')

        x = input('Enter any character to cancel reservation: ')

        cancel_res = cancel(_search_data, _booking_data, _token)
        if not cancel_res.get('status'):
            raise Exception(cancel_res.get('error'))

        print('>> Cancelled successfully')
    except Exception as ex:
        print(ex)
    finally:
        logout()
