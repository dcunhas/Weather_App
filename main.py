import math

from nicegui import  ui, app
import datetime
import usaddress
from requests import HTTPError
import re
import get_weather
import mapping

app.add_static_files('/weather_icons', 'icons/makin_things_icons')
ui.colors(primary='#555')

class Location():
    def __init__(self, name, lat, lon):
        self.name = name
        self.lat = lat
        self.lon = lon

class DarkButton(ui.button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._dark = ui.dark_mode() 
        self._state = True #app.storage.browser.get('dark_mode', True)
        self.on('click', self.toggle)
        self._dark.enable() if self._state else self._dark.disable()
        self.props('round size="xs"')

    def toggle(self) -> None:
        """Toggle the button state."""
        self._state = not self._state
        #app.storage.browser['dark_mode'] = self._state
        self._dark.toggle()
        self.update()

    def update(self) -> None:
        if self._state:
            self.props('icon="dark_mode" color="white" text-color="black"')
        else:
            self.props('icon="light_mode" color="black" text-color="white"')
        super().update()

@ui.page('/')
async def weather_page():
    class DailyWeather(ui.card):
        def __init__(self, date=None, high=None, low=None, precipitation=None, icon=None, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.__enter__()
            self.classes('bg-info').style('height: 100%; flex: 0 0 10em; flex-direction: row;')
            with ui.element().classes('divide-y'):#.style('flex-shrink: 0;'):
                with ui.row().classes('full-width').style('white-space:nowrap;'):
                    self.icon = ui.icon(icon).classes('text-7xl').style('margin-left:-15px; display: inline-block;')
                    with ui.card().tight().style('display: inline-block; position:absolute; margin-left:45px; white-space: nowrap;'):
                        self.high_label = ui.label(high).classes('text-h6').style('display: inline-block; vertical-align: top; margin-top: 3px;')
                        ui.label('\N{SOLIDUS}').style('display: inline-block; font-size: 50px; vertical-align: top; margin-top: -15px; margin-right: -5px; margin-left:-5px')
                        self.low_label = ui.label(low).classes('').style('display: inline-block; vertical-align: bottom;  margin-bottom: 10px')
                with ui.row().style('width: 7.7em'):
                    ui.icon('water_drop')
                    self.precipitation = ui.label(precipitation)
                with ui.row().style('width: 7.7em'):
                    self.date_label = ui.label(date).classes('text-overline')


            self.__exit__()
        def update(self, date=None, high=None, low=None, precipitation=None, icon=None):
            self.__enter__()
            if date:
                self.date_label.set_text(date)
            if high:
                self.high_label.set_text(high)
            if low:
                self.low_label.set_text(low)
            if precipitation:
                self.precipitation.set_text(precipitation)
            if icon:
                self.icon.set_name(icon)
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

    #Based on https://www.reddit.com/r/nicegui/comments/145d6z6/how_to_read_the_users_geolocation/
    async def get_browser_location():
        response = await ui.run_javascript(''' 
            return await new Promise(
                (resolve, reject) => {
                    if (!navigator.geolocation) {
                        reject(new Error('Geolocation is not supported by your browser')); 
                    } 
                    else {
                        navigator.geolocation.getCurrentPosition( (position) => {
                            resolve({
                                latitude: position.coords.latitude, 
                                longitude: position.coords.longitude, 
                            }); 
                        }, () => {
                            reject(new Error('Unable to retrieve your location')); 
                        }); 
                    }
                }); 
          ''', timeout=5.0)
        return (response["latitude"], response["longitude"])

    async def on_get_browser_location():
        try:
            (lat, lon) = await get_browser_location()
        except Exception as e:
            print(e)
            ui.notify('Could not get location')
            return
        print(f'Browser Location: ({lat}, {lon})')
        await update_weather(lat_lon=(lat, lon))

    async def on_temp_scale_toggle():
        print('toggled temp scale')
        await update_weather(use_previous_location=True)
        #app.storage.browser['temp_scale'] = temp_scale_selector.value

    async def weather_from_rough_location():
        rough_ip_location = get_weather.get_location()
        await update_weather(place_name=rough_ip_location['city'], state_name=rough_ip_location['region'],
                             country_name=rough_ip_location['country'])

    with ui.footer(value=False) as footer:
        ui.label('Footer')


    # Create Left Menu Drawer closed
    with ui.left_drawer(value=False).classes('bg-blue-100') as left_drawer:
        ui.label('Side menu')


    with ui.header() as header:
        with ui.row().classes('w-full') as header_row_1:
            #ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
            with ui.link(target='/').classes('justify-left').style('text-decoration: none; '):
                ui.label('Weather Stuff').classes('text-h3')
            #ui.space()
            with ui.element('div').classes('absolute-center').style('display: flex; align-items: flex-start;'):
                set_location_input = ui.input(label='Location').on(
                    'keydown.enter',
                    lambda e: update_weather(e.sender.value))# .on('blur', lambda e: update_weather(e.sender.value))
                ui.button(on_click=on_get_browser_location, icon='location_on').props('round dense color=accent size="sm"').style('margin-top: 1.5em')
            #ui.space()
            with ui.element('div').classes('absolute-right').style('margin-top: 1em; margin-right: 1em'):
                temp_scale_selector = ui.toggle(
                    {'F': u'\N{DEGREE SIGN}F', 'C': u'\N{DEGREE SIGN}C'}, value='F',
                    on_change=on_temp_scale_toggle).props('rounded color="dark" toggle-color="positive"')
                DarkButton().classes('justify-right')
        with ui.row().classes('w-full') as header_row_2:
            with ui.column() as location_div:
                with ui.row():
                    ui.label('Location: ')
                    location_label = ui.label('')


    with ui.tabs() as tabs:
        ui.tab('Today')
        ui.tab('Hourly')
        ui.tab('Seven Days')


    with ui.tab_panels(tabs, value='Today').classes('w-full'):
        with ui.tab_panel('Today'):
            with ui.grid(columns='1fr 2fr'):
                with ui.card().classes('bg-info'):
                    today_location = ui.label('').classes('text-overline')
                    with ui.grid(columns='25% 75%').style('width: 100%;'):
                        today_image = ui.image('')
                        today_temp = ui.label('').classes('text-h4 q-pa-sm text-accent').style('width: max-content;')
                    with ui.column().classes('divide-y full-width'):
                        with ui.row().classes(' full-width'):
                            ui.label('Humidity')
                            ui.space()
                            today_humidity = ui.label('')
                        with ui.row().classes(' full-width'):
                            with ui.element():
                                ui.label('Precipitation').style('display:inline;')
                                ui.icon('water_drop')
                            ui.space()
                            today_precipitation = ui.label('')
                        with ui.row().classes(' full-width'):
                            ui.label('Feels Like')
                            ui.space()
                            today_feels_like = ui.label('')
                        #today_weather_map = ui.image('')
                today_weather_map = ui.html('')

        with ui.tab_panel('Hourly'):
            with ui.row() as hourly_list_header:
            #     ui.label('Time')
            #     ui.label('Temperature')
            #     ui.label('Precipitation')
            #     ui.label('Feels Like')
            # hourly_weather_cards = [HourlyWeather() for i in range(40)]
                hourly_weather_columns = [
                    {'name': 'day', 'label': 'Day', 'field': 'day'},
                    {'name': 'time', 'label': 'Time', 'field': 'time'},
                    {'name': 'weather_icon', 'label': 'Weather', 'field': 'weather_icon'},
                    {'name': 'temperature', 'label': 'Temperature', 'field': 'temperature'},
                    {'name': 'feels_like', 'label': 'Feels Like', 'field': 'feels_like'},
                    {'name': 'precipitation', 'label': 'Precipitation', 'field': 'precipitation'},
                    {'name': 'humidity', 'label': 'Humidity', 'field': 'humidity'},
                ]
                hourly_weather_table = ui.table(columns=hourly_weather_columns, rows=[])
                hourly_weather_table.add_slot('body-cell-weather_icon', r'''
                                        <q-td key="weather_icon" :props="props">
                                            <div>
                                                <img :src="props.row.weather_icon"/> 
                                            </div>
                                        </q-td>
                                    ''')
            hourly_weather_table.add_slot('body-cell-precipitation', r'''
                                                    <q-td key="precipitation" :props="props">
                                                        {{ props.row.precipitation }}
                                                        <q-icon name="water_drop"/>
                                                    </q-td>
                                                ''')
        with ui.tab_panel('Seven Days'):
            with ui.row().classes('no-wrap flex full-width') as multi_day_forcast:
                multi_day_weather_cards = [DailyWeather() for i in range(7)]
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
    last_weather_unit = temp_scale_selector.value
    async def update_weather(location_string='', place_name='', state_name='', country_name='', zip_code='', lat_lon=None, use_previous_location=False):
        if not (use_previous_location or location_string.strip() or place_name or state_name or country_name or zip_code or lat_lon):
            return
        #Don't update if updated recently with same query
        nonlocal last_updated_weather_time, last_weather_location, last_weather_unit
        update_time = datetime.datetime.now()
        if (not use_previous_location and
                last_weather_location and
                (last_weather_location.name == location_string) and
                last_updated_weather_time and
                (last_updated_weather_time - update_time) < datetime.timedelta(seconds=10) and
                last_weather_unit == temp_scale_selector.value):
            return
        loading_dialog.open()
        if use_previous_location:
            if last_weather_location is None:
                return
            (lat, lon) = (last_weather_location.lat, last_weather_location.lon)
            open_weather_geocode = get_weather.get_open_weather_reverse_geocode(lat, lon)
            print(open_weather_geocode)
        elif lat_lon:
            print('lat lon')
            (lat, lon) = lat_lon
            if last_weather_location and (last_weather_location.lat == lat) and \
                    (last_weather_location.lon == lon):
                return
            open_weather_geocode = get_weather.get_open_weather_reverse_geocode(lat, lon)
        else:
            (tagged_location, location_type) = usaddress.tag(location_string)
            if place_name:
                tagged_location['PlaceName'] = place_name
            if state_name:
                tagged_location['StateName'] = state_name
            if country_name:
                tagged_location['CountryName'] = country_name
            if zip_code:
                tagged_location['ZipCode'] = zip_code
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
            except Exception as e:
                print(e)
                loading_dialog.close()
                general_error_dialog.open()
                return
            (lat, lon) = (open_weather_geocode['lat'], open_weather_geocode['lon'])
        try:
            open_weather_current = get_weather.get_open_weather_current_weather(lat, lon, units=get_weather.open_weather_units[temp_scale_selector.value])
            open_weather_five_day = get_weather.get_open_weather_five_day_forcast(lat, lon, units=get_weather.open_weather_units[temp_scale_selector.value])
            open_meteo_weather = get_weather.get_openmeteo_weather(lat, lon, get_weather.open_meteo_units[temp_scale_selector.value])
        except HTTPError as e:
            print('Weather Data problem')
            loading_dialog.close()
            request_error_dialog.open()
            return
        except Exception as e:
            print(e)
            loading_dialog.close()
            general_error_dialog.open()
            return

        try:
            gov_weather_alerts = get_weather.get_alerts_gov_weather(lat, lon)
            gov_weather = get_weather.get_weather_gov_weather(lat, lon)
            gov_county_link = gov_weather['properties']['county']
            county_code_match = re.match(r'https://api\.weather\.gov/zones/county/(.*)/?', gov_county_link)
            if not county_code_match:
                print('Could not find match from county code url:', gov_county_link)
            gov_county_code = county_code_match.group(1)
            gov_weather_alerts_zone = get_weather.get_alerts_gov_weather_zone(gov_county_code)
        except HTTPError as e:
            print('Government data problem')
            loading_dialog.close()
            request_error_dialog.open()
            return
        except Exception as e:
            print(e)
            loading_dialog.close()
            general_error_dialog.open()
            return
        loading_dialog.close()
        last_updated_weather_time = update_time
        last_weather_location = Location(location_string, lat, lon)
        last_weather_unit = temp_scale_selector.value
        location_label.set_text(f'{open_weather_geocode["name"]} ({round(lat, 2)}' + u"\N{DEGREE SIGN}N"+ f', {round(lon, 2)}' + u"\N{DEGREE SIGN}E)")
        today_location.set_text(open_weather_geocode['name'])
        today_image.set_source(f'https://openweathermap.org/img/wn/{open_weather_current["weather"][0]["icon"]}@2x.png')
        today_temp.set_text(str(round(open_weather_current['main'].get('temp', -100))) + u'\N{DEGREE SIGN}')
        today_humidity.set_text(f"{open_weather_current['main'].get('humidity', 'NaN')}%")
        today_feels_like.set_text(str(open_weather_current['main'].get('feels_like', 'NaN')) + u'\N{DEGREE SIGN}')
        if 'rain' in open_weather_current:
            today_precipitation.set_text(f'{open_weather_current["rain"].get("1h", "0")} mm')
        else:
            today_precipitation.set_text('0 mm')
        timezone = datetime.timezone(datetime.timedelta(seconds=open_weather_five_day['city']['timezone']))
        hourly_weather_rows = [{
            'id': i,
            'day': datetime.datetime.fromtimestamp(future_forcast.get('dt', ''), tz=timezone).strftime('%a %b %d'),
            'time': datetime.datetime.fromtimestamp(future_forcast.get('dt', ''), tz=timezone).strftime('%I:%M%p'),
            'temperature': str(round(future_forcast['main']['temp'])) + u'\N{DEGREE SIGN}' if 'temp' in future_forcast['main'] else 'NaN',
            'feels_like': str(round(future_forcast['main']['feels_like'])) + u'\N{DEGREE SIGN}' if 'feels_like' in future_forcast['main'] else 'NaN',
            'precipitation': str(round(future_forcast['pop'] * 100)) + '%' if 'pop' in future_forcast else 'NaN',
            'weather_icon': f'https://openweathermap.org/img/wn/{future_forcast["weather"][0]["icon"]}.png',
            'humidity': str(round(future_forcast['main']['humidity'])) + '%' if 'humidity' in future_forcast['main'] else 'NaN',
        }
           for i, future_forcast in zip(range(len(open_weather_five_day['list'])), open_weather_five_day['list'])]
        hourly_weather_table.clear()
        hourly_weather_table.update_rows(hourly_weather_rows)
        num_days = len(open_meteo_weather['Daily']['Dates'])
        for i, md_weather_card, in zip(range(num_days), multi_day_weather_cards):
            weather_date = open_meteo_weather['Daily']['Dates'][i].astimezone(timezone)
            md_weather_card.update(date=weather_date.strftime('%a %m/%d'),
                                   high=str(round(open_meteo_weather['Daily']['Max Temperature'][i])) + '\N{DEGREE SIGN}',
                                   low=str(round(open_meteo_weather['Daily']['Min Temperature'][i])) + '\N{DEGREE SIGN}',
                                   precipitation=str(round(open_meteo_weather['Daily']['Min Temperature'][i])) + '%',
                                   icon=f'img:weather_icons/{get_weather.weather_code_icon_dict[open_meteo_weather["Daily"]["Weather Code"][i]]}.svg')



        # for future_forcast, hourly_weather_card in zip(open_weather_five_day['list'], hourly_weather_cards):
        #     hourly_weather_card.update(time=datetime.datetime.fromtimestamp(future_forcast['dt'], tz=timezone).strftime('%I:%M%p %a %b %d'),
        #                                temperature=future_forcast['main']['temp'],
        #                                feels_like=future_forcast['main']['feels_like'],
        #                                precipitation=future_forcast['pop'])
        today_weather_map.set_content(mapping.map_iframe(lat, lon))
        #today_weather_map.set_source(open_weather_map)
        # for (daily_weather, daily_weather_card) in zip(new_weather.daily_forecasts, multi_day_weather_cards):
        #     daily_weather_card.update(date=daily_weather.date, high=daily_weather.highest_temperature, low=daily_weather.lowest_temperature)
    await weather_from_rough_location()
    # with ui.table(title='Ten Day Forcast',
    #               columns=[{'name': 'day', 'label': '', 'field': 'day'},
    #                        {'name': 'weather', 'label': '', 'field': 'weather'}],
    #               rows=[{'day': str(i), 'weather': "Cold"} for i in range(10)]).props('grid') as ten_day_forcast:
    #    pass

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(storage_secret='0')





