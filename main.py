from nicegui import Tailwind, ui

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
    def __init__(self, date, high, low, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__enter__()
        ui.label(date)
        ui.label(high)
        ui.label(low)
        self.__exit__()

class HourlyWeather(ui.row):
    def __init__(self, time, temperature, precipitation=None, *args, **kwargs) -> None:
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
            location = ui.label('Madison')
            set_location_input = ui.input(label='Location')


with ui.tabs() as tabs:
    ui.tab('Today')
    ui.tab('Hourly')
    ui.tab('Ten Day')


with ui.tab_panels(tabs, value='Today').classes('w-full'):
    with ui.tab_panel('Today'):
        with ui.card():
            ui.label('Today\'s Weather')
    with ui.tab_panel('Hourly'):
        for i in range(24):
            HourlyWeather(i, 24)
    with ui.tab_panel('Ten Day'):
        with ui.row().classes('no-wrap justify-center') as ten_day_forcast:
            for i in range(10):
                DailyWeather('Monday', '72', '12').classes('col')
        with ui.expansion().props('hide-expand-icon') as daily_info_expansion:
            ui.label('Weather Info')





# with ui.table(title='Ten Day Forcast',
#               columns=[{'name': 'day', 'label': '', 'field': 'day'},
#                        {'name': 'weather', 'label': '', 'field': 'weather'}],
#               rows=[{'day': str(i), 'weather': "Cold"} for i in range(10)]).props('grid') as ten_day_forcast:
#    pass

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()