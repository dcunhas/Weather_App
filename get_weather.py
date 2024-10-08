import requests
import requests_cache
from retry_requests import retry
import openmeteo_requests
import os
import math
import pandas as pd

open_weather_api_key = os.environ['OPEN_WEATHER_API_KEY']
open_weather_units = {'F': 'imperial', 'C': 'metric', 'K': 'standard'}
open_meteo_units =  {'F': 'fahrenheit', 'C': 'celsius'}


def get_open_weather_geocode(tagged_location):
    if 'ZipCode' in tagged_location:
        result = requests.get('http://api.openweathermap.org/geo/1.0/zip', {
            'zip': f'{tagged_location["ZipCode"]},{"US"}',
            'appid': open_weather_api_key,
            'limit': 1
        }, timeout=3)
        result.raise_for_status()
        return result.json()
    elif 'PlaceName' in tagged_location:
        result = requests.get('http://api.openweathermap.org/geo/1.0/direct', {
            'q': f'{tagged_location["PlaceName"]},{tagged_location.get("StateName", "")},{tagged_location.get("CountryName", "US")}',
            'appid': open_weather_api_key,
            'limit': 1
        }, timeout=3)
        result.raise_for_status()
        try:
            return result.json()[0]
        except IndexError:
            raise ValueError('Could not find location')
    else:
      raise ValueError('Missing required fields in tagged_location')


def get_open_weather_reverse_geocode(lat, lon):
    print(lat, lon)
    result = requests.get('http://api.openweathermap.org/geo/1.0/reverse', {
        'lat': lat,
        'lon': lon,
        'appid': open_weather_api_key,
        'limit': 1
    }, timeout=3)
    return result.json()[0]

#Units can be 'imperial', 'metric', or 'standard' (i.e. Kelvin)
def get_open_weather_five_day_forcast(lat, lon, units='imperial'):
    if units not in ['imperial', 'metric', 'standard']:
        raise ValueError("Unknown Units Type")
    result = requests.get('https://api.openweathermap.org/data/2.5/forecast', {
        'lat': lat,
        'lon':lon,
        'units':units,
        'appid': open_weather_api_key,
    }, timeout=3)
    result.raise_for_status()
    return result.json()


#Units can be 'imperial', 'metric', or 'standard' (i.e. Kelvin)
def get_open_weather_current_weather(lat, lon, units='imperial'):
    if units not in ['imperial', 'metric', 'standard']:
        raise ValueError("Unknown Units Type")
    result = requests.get('https://api.openweathermap.org/data/2.5/weather', {
        'lat': lat,
        'lon':lon,
        'units':units,
        'appid': open_weather_api_key,
    }, timeout=3)
    result.raise_for_status()
    return result.json()

#Based on mercator projection code from https://developers.google.com/maps/documentation/javascript/examples/map-coordinates
def mercator_projection(lat, lon, tile_size=256):
    siny = math.sin(lat * math.pi / 180)
    siny = min([max([siny, -0.9999]), 0.9999])
    return (tile_size * (0.5 + lon / 360), tile_size * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)))


#Based on https://www.freecodecamp.org/news/how-to-get-location-information-of-ip-address-using-python/
def get_ip():
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response["ip"]

def get_location():
    ip_address = get_ip()
    response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
    location_data = {
        "ip": ip_address,
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country_name")
    }
    return location_data


def get_openmeteo_weather(lat, lon, temp_unit='fahrenheit'):
    if temp_unit not in ['fahrenheit', 'celsius']:
        raise ValueError('Unknown Temperature Unit')

    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "rain"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation_probability",
                   "precipitation"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "apparent_temperature_max",
                  "apparent_temperature_min", "precipitation_probability_max", "weather_code"],
        "temperature_unit": temp_unit
    }
    response = openmeteo.weather_api(url, params=params)[0]
    weather_dict = {}
    daily = response.Daily()
    weather_dict['Daily'] = {}
    weather_dict['Daily']['Max Temperature'] = daily.Variables(0).ValuesAsNumpy().tolist()
    weather_dict['Daily']['Min Temperature'] = daily.Variables(1).ValuesAsNumpy().tolist()
    weather_dict['Daily']['Max Apparent Temperature'] = daily.Variables(2).ValuesAsNumpy().tolist()
    weather_dict['Daily']['Min Apparent Temperature'] = daily.Variables(3).ValuesAsNumpy().tolist()
    weather_dict['Daily']['Precipitation Chance'] = daily.Variables(4).ValuesAsNumpy().tolist()
    weather_dict['Daily']['Weather Code'] = daily.Variables(5).ValuesAsNumpy().astype(int).tolist()
    timestamps = pd.date_range(start=pd.to_datetime(daily.Time(), unit='s', utc=True),
                                                   end=pd.to_datetime(daily.TimeEnd(), unit='s', utc=True),
                                                   freq=pd.Timedelta(seconds=daily.Interval())).tolist()
    dates = [ts.to_pydatetime() for ts in timestamps]
    weather_dict['Daily']['Dates'] = dates
    return weather_dict


def get_weather_gov_weather(lat, lon):
    response = requests.get(f'https://api.weather.gov/points/{lat},{lon}').json()
    return response


def get_alerts_gov_weather(lat, lon):
    response = requests.get(f'https://api.weather.gov/alerts/active', {'point': f'{lat},{lon}'}).json()
    return response

def get_alerts_gov_weather_zone(zone):
    response = requests.get(f'https://api.weather.gov/alerts/active', {'zone': zone}).json()
    return response


#Takes WMO weather numeric code and returns material icon name if available
weather_code_icon_dict = {
    0: 'clear-day',
    1: 'cloudy-1-day',
    2: 'cloudy-1-day',
    3: 'cloudy',
    45: 'fog',
    48: 'fog',
    51: 'rainy-1',
    53: 'rainy-1',
    55: 'rainy-1',
    56: 'rain-and-sleet-mix',
    57: 'rain-and-sleet-mix',
    61: 'rainy-2',
    63: 'rainy-2',
    65: 'rainy-3',
    66: 'rain-and-sleet-mix',
    67: 'rain-and-sleet-mix',
    71: 'snowy-1',
    73: 'snowy-2',
    75: 'snowy-3',
    77: 'snowy-1',
    80: 'rainy-3',
    81: 'rainy-3',
    82: 'rainy-3',
    85: 'snowy-3',
    86: 'snowy-3',
    95: 'thunderstorms',
    96: 'hail',
    99: 'hail'
}