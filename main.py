from nicegui import Tailwind, ui
import get_weather
import asyncio


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
    def __init__(self, time=None, temperature=None, precipitation=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__enter__()
        ui.label(time)
        ui.label(temperature)
        ui.label(precipitation)
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
            'blur', lambda e: update_weather(e.value)).on(
            'keydown.enter', lambda e: location_label.set_text(e.value))


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
            
            
    with ui.tab_panel('Hourly'):
        for i in range(24):
            HourlyWeather(i, 24)
    with ui.tab_panel('Three Days'):
        with ui.row().classes('no-wrap justify-center') as three_day_forcast:
            three_day_weather_cards = [DailyWeather().classes('col') for i in range(3)]
        with ui.expansion().props('hide-expand-icon') as daily_info_expansion:
            ui.label('Weather Info')
            
            
    async def update_weather(location):
        new_weather = await get_weather.get_weather(location)
        print(new_weather)
        location_label.set_text(new_weather.location)
        today_location.set_text(new_weather.location)
        today_temp.set_text(new_weather.temperature)
        today_humidity.set_text(new_weather.humidity)
        today_precipitation.set_text(new_weather.precipitation)
        for (daily_weather, daily_weather_card) in zip(new_weather.daily_forecasts, three_day_weather_cards):
            daily_weather_card.update(date=daily_weather.date, high=daily_weather.highest_temperature, low=daily_weather.lowest_temperature)
    



# with ui.table(title='Ten Day Forcast',
#               columns=[{'name': 'day', 'label': '', 'field': 'day'},
#                        {'name': 'weather', 'label': '', 'field': 'weather'}],
#               rows=[{'day': str(i), 'weather': "Cold"} for i in range(10)]).props('grid') as ten_day_forcast:
#    pass

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()