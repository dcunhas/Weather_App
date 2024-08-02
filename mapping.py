import folium

def map_iframe(lat, lon, zoom=7):
    map = folium.Map((lat, lon), min_zoom=7, max_zoom=7, min_lat=lat,
                     max_lat=lat, min_lon=lon, max_lon=lon,
                     zoom_control=False, dragging=False)
    map.get_root().width = "200px"
    map.get_root().height = "200px"
    iframe = map.get_root()._repr_html_()
    return iframe
