import folium
from get_weather import open_weather_api_key

def map_iframe(lat, lon, zoom=7):
    map = folium.Map((lat, lon), min_zoom=7, max_zoom=7,
                     zoom_control=False, dragging=False, doubleClickZoom=False, boxZoom=False, scrollWheelZoom=False,
                     keyboard=False, touchZoom=False)
    #map.get_root().width = "200px"
    #map.get_root().height = "200px"
    folium.TileLayer('https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid='+ open_weather_api_key,
                     name='Clouds', attr='Weather data provided by OpenWeather', overlay=True, show=True).add_to(map)
    folium.TileLayer('https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid='+ open_weather_api_key,
                     name='Precipitation', attr='Weather data provided by OpenWeather', overlay=True, show=True).add_to(map)
    folium.TileLayer('https://tile.openweathermap.org/map/pressure_new/{z}/{x}/{y}.png?appid='+ open_weather_api_key,
                     name='Pressure', attr='Weather data provided by OpenWeather', overlay=True, show=False).add_to(map)
    folium.TileLayer('https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid='+ open_weather_api_key,
                     name='Wind', attr='Weather data provided by OpenWeather', overlay=True, show=False).add_to(map)
    folium.TileLayer('https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid='+ open_weather_api_key,
                     name='Temperature', attr='Weather data provided by OpenWeather', overlay=True, show=False).add_to(map)
    folium.LayerControl().add_to(map)
    iframe = map.get_root()._repr_html_()
    return iframe
