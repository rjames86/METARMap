# How many seconds between each screen
CYCLE_TIME = 4

SMALL_FONT_SIZE = 12
LARGE_FONT_SIZE = 36

# Must be any of
#    dewpoint_c
#    elevation_m
#    flight_category
#    latitude
#    longitude
#    maxT_c
#    metar_type
#    minT_c
#    observation_time
#    sea_level_pressure_mb
#    station_id
#    temp_c
#    visibility_statute_mi
#    wind_dir_degrees
#    wind_speed_kt
#    wind_and_speed
#    sea_level_pressure_hg
#   raw_text
DISPLAY_VALUES = [
    "observation_time",
    "wind_and_speed",
    "flight_category",
    "sky_condition",
    "temp_c",
    "sea_level_pressure_hg",
    "raw_text",
]