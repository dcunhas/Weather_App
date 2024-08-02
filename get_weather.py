import python_weather
import requests
import asyncio
import os
import json
import math
from PIL import Image
from io import BytesIO

open_weather_api_key = os.environ['OPEN_WEATHER_API_KEY']
open_weather_units = {'F': 'imperial', 'C': 'metric', 'K': 'standard'}

async def get_weather(location):
    # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        # fetch a weather forecast from a city
        weather = await client.get(location)
        return weather


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
            'q': f'{tagged_location["PlaceName"]},{tagged_location.get("StateName", "")},{"US"}',
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

# Calculations based on https://developers.google.com/maps/documentation/javascript/coordinates?hl=en
def get_open_weather_map(lat, lon, cloud_layer=True,
                         precipitation_layer=True, pressure_layer=True,
                         wind_layer=True, temp_layer=True, z=0):
    get_layer_bool = [cloud_layer, precipitation_layer, pressure_layer, wind_layer, temp_layer]
    possible_layers = ['clouds_new', 'precipitation_new', 'pressure_new', 'wind_new', 'temp_new']
    layers = [p for (p, b) in zip(possible_layers, get_layer_bool) if b]
    tile_size = 256
    (world_x, world_y) = mercator_projection(lat, lon)
    (pixel_x, pixel_y) = (world_x * (2**z), world_y * (2**z))
    (tile_x, tile_y) = (int(pixel_x / tile_size), int(pixel_y / tile_size))

    result = requests.get()

    for layer in layers:
        result = requests.get(f'https://tile.openweathermap.org/map/{layer}/{z}/{tile_x}/{tile_y}.png', {
            'appid': open_weather_api_key,
        })
        result.raise_for_status()
        layer_image = Image.open(BytesIO(result.content))

    map_image = Image.open(BytesIO(result.content))
    return map_image
