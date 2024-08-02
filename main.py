from nicegui import Tailwind, ui
import asyncio
import datetime
import usaddress
from requests import HTTPError

import get_weather
import mapping
class DarkButton(ui.button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._dark = ui.dark_mode() 
        self._state = True
        self.on('click', self.toggle)
        self._dark.enable() if self._state else self._dark.disable()
        self.props('round size="xs"')

    def toggle(self) -> None:
        """Toggle the button state."""
        self._state = not self._state
        self._dark.toggle()
        self.update()

    def update(self) -> None:
        if self._state:
            self.props('icon="dark_mode" color="white" text-color="black"')
        else:
            self.props('icon="light_mode" color="black" text-color="white"')
        super().update()

class DailyWeather(ui.card):
    def __init__(self, date=None, high=None, low=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__enter__()
        self.date_label = ui.label(date)
        self.high_label = ui.label(high)
        self.low_label = ui.label(low)
        self.__exit__()
    def update(self, date=None, high=None, low=None):
        self.__enter__()
        if date:
            self.date_label.set_text(date)
        if high:
            self.high_label.set_text(high)
        if low:
            self.low_label.set_text(low)
        self.__exit__()

class HourlyWeather(ui.row):
    def __init__(self, time=None, temperature=None, precipitation=None, feels_like=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__enter__()
        self.time_label = ui.label(time)
        self.temp_label = ui.label(temperature)
        self.prec_label = ui.label(precipitation)
        self.feels_like_label = ui.label(feels_like)
        self.__exit__()
    def update(self, time=None, temperature=None, precipitation=None, feels_like=None):
        self.__enter__()
        if time:
            self.time_label.set_text(time)
        if temperature:
            self.temp_label.set_text(temperature)
        if precipitation:
            self.prec_label.set_text(precipitation)
        if feels_like:
            self.feels_like_label.set_text(feels_like)
        self.__exit__()

with ui.footer(value=False) as footer:
    ui.label('Footer')


# Create Left Menu Drawer closed
with ui.left_drawer(value=False).classes('bg-blue-100') as left_drawer:
    ui.label('Side menu')


with ui.header() as header:
    with ui.row().classes('w-full') as header_row_1:
        ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
        with ui.link(target='/'):
            ui.label('Weather Stuff')
        ui.space()
        DarkButton().classes('float-right')
    with ui.row().classes('w-full') as header_row_2:
        with ui.row() as location_div:
            ui.label('Location: ')
            location_label = ui.label('')
            set_location_input = ui.input(label='Location').on(
            'keydown.enter', lambda e: update_weather(e.sender.value))#.on('blur', lambda e: update_weather(e.sender.value))


with ui.tabs() as tabs:
    ui.tab('Today')
    ui.tab('Hourly')
    ui.tab('Three Days')


with ui.tab_panels(tabs, value='Today').classes('w-full'):
    with ui.tab_panel('Today'):
        with ui.card():
            today_location = ui.label('').classes('h3')
            ui.label('Temperature')
            today_temp = ui.label('')
            ui.label('Humidity')
            today_humidity = ui.label('')
            ui.label('Precipitation')
            today_precipitation = ui.label('')
            ui.label('Feels Like')
            today_feels_like = ui.label('')
            #today_weather_map = ui.image('')
            today_weather_map = ui.html('')
            
    with ui.tab_panel('Hourly'):
        hourly_weather_cards = [HourlyWeather() for i in range(40)]
    with ui.tab_panel('Three Days'):
        with ui.row().classes('no-wrap justify-center') as multi_day_forcast:
            multi_day_weather_cards = [DailyWeather().classes('col') for i in range(5)]
        with ui.expansion().props('hide-expand-icon') as daily_info_expansion:
            ui.label('Weather Info')
            
with ui.dialog().props('persistent') as loading_dialog, ui.card():
    ui.label('Loading')
    ui.spinner(size='lg')
with ui.dialog() as bad_location_dialog, ui.card():
    ui.label('Error: Could not find location. Please try again.')
    ui.button('Close', on_click=bad_location_dialog.close)
with ui.dialog() as request_error_dialog, ui.card():
    ui.label('Error: Error communicating with server. Please try again later.')
    ui.button('Close', on_click=request_error_dialog.close)
with ui.dialog() as general_error_dialog, ui.card():
    ui.label('Error: An Error was encountered. Please try again later.')
    ui.button('Close', on_click=general_error_dialog.close)

last_updated_weather_time = None
last_weather_location = None
async def update_weather(location):
    if not location.strip():
        return
    #Don't update if updated recently with same query
    global last_updated_weather_time, last_weather_location
    update_time = datetime.datetime.now()
    if (last_weather_location and (last_weather_location == location) and last_updated_weather_time and
            (last_updated_weather_time - update_time) < datetime.timedelta(seconds=10)):
        return
    loading_dialog.open()
    (tagged_location, location_type) = usaddress.tag(location)
    try:
        open_weather_geocode = get_weather.get_open_weather_geocode(tagged_location)
    except ValueError as e:
        loading_dialog.close()
        bad_location_dialog.open()
        return
    except HTTPError as e:
        loading_dialog.close()
        request_error_dialog.open()
        return
    except Exception:
        loading_dialog.close()
        general_error_dialog.open()
        return
    (lat, lon) = (open_weather_geocode['lat'], open_weather_geocode['lon'])
    try:
        open_weather_current = get_weather.get_open_weather_current_weather(lat, lon)
        open_weather_five_day = get_weather.get_open_weather_five_day_forcast(lat, lon)
        #open_weather_map = get_weather.get_open_weather_map(lat, lon)
    except HTTPError as e:
        loading_dialog.close()
        request_error_dialog.open()
        return
    except Exception:
        loading_dialog.close()
        general_error_dialog.open()
        return

    new_weather = await get_weather.get_weather(location)
    loading_dialog.close()
    last_updated_weather_time = update_time
    last_weather_location = location
    location_label.set_text(open_weather_geocode['name'])
    today_location.set_text(open_weather_geocode['name'])
    today_temp.set_text(open_weather_current['main']['temp'])
    today_humidity.set_text(open_weather_current['main']['humidity'])
    today_feels_like.set_text(open_weather_current['main']['feels_like'])
    if 'rain' in open_weather_current:
        today_precipitation.set_text(f'{open_weather_current["rain"].get("1h", "0")} mm')
    else:
        today_precipitation.set_text('0 mm')
    timezone = datetime.timezone(datetime.timedelta(seconds=open_weather_five_day['city']['timezone']))
    for future_forcast, hourly_weather_card in zip(open_weather_five_day['list'], hourly_weather_cards):
        hourly_weather_card.update(time=datetime.datetime.fromtimestamp(future_forcast['dt'], tz=timezone),
                                   temperature=future_forcast['main']['temp'],
                                   feels_like=future_forcast['main']['feels_like'],
                                   precipitation=future_forcast['pop'])
    today_weather_map.set_content(mapping.map_iframe(lat, lon))
    #today_weather_map.set_source(open_weather_map)
    # for (daily_weather, daily_weather_card) in zip(new_weather.daily_forecasts, multi_day_weather_cards):
    #     daily_weather_card.update(date=daily_weather.date, high=daily_weather.highest_temperature, low=daily_weather.lowest_temperature)




# with ui.table(title='Ten Day Forcast',
#               columns=[{'name': 'day', 'label': '', 'field': 'day'},
#                        {'name': 'weather', 'label': '', 'field': 'weather'}],
#               rows=[{'day': str(i), 'weather': "Cold"} for i in range(10)]).props('grid') as ten_day_forcast:
#    pass

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()

