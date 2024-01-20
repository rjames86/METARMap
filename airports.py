import os
from asyncio import sleep

from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE

import astral
from astral.sun import sun as AstralSun
import datetime



class AirportLED:
    def __init__(self, strip, pixel_index, airport_code, metar_info):
        self.strip = strip
        self.pixel_index = pixel_index
        self.airport_code = airport_code
        self.metar_info = metar_info

        if self.metar_info is None:
            self.color = WHITE
            self.city = None
        else:
            self.color = FLIGHT_CATEGORY_TO_COLOR.get(self.metar_info.flightCategory, WHITE)
            self.city = astral.LocationInfo(timezone='UTC', latitude=self.metar_info.latitude, longitude=self.metar_info.longitude)


    def __repr__(self):
        return f'AirportLED<{self.airport_code}>'
    
    """
    Figure out how bright the light should be based on time of day
    """
    def determine_brightness(self, color):
        if self.city is None:
            return color
        G, R, B = color
        dimming_level = 1

        print(self.airport_code, self.metar_info.observation_time)

        try:
            sun = AstralSun(self.city.observer, tzinfo=self.city.tzinfo)
            print(sun)
            # It's probably dark out
            if self.metar_info.observation_time < sun['dawn'] or self.metar_info.observation_time > sun['dusk']:
                print("before dawn or after dusk")
                dimming_level = 0.1
            elif sun['dawn'] < self.metar_info.observation_time < sun['noon']:
                print("between dawn and noon")
                total_seconds = sun['noon'] - sun['dawn']
                seconds_until_noon = sun['noon'] - self.metar_info.observation_time
                dimming_level = seconds_until_noon / total_seconds
            elif sun['noon'] < self.metar_info.observation_time < sun['dusk']:
                print("between noon and dusk")
                total_seconds = sun['dusk'] - sun['noon']
                seconds_until_dusk = sun['dusk'] - self.metar_info.observation_time
                dimming_level = seconds_until_dusk / total_seconds

            return (G * dimming_level, R * dimming_level, B * dimming_level)
        except Exception as e:
            print("Failed set brightness", self.airport_code, self.metar_info.observation_time)
            return WHITE



    async def run(self):
        while True:
            print("running for ", self.airport_code)
            if self.metar_info is None:
                print("no metar info found for %s. Returning..." % self.airport_code)
                await sleep(0)
            if self.metar_info.flightCategory is None:
                await sleep(0)
            
            print(
                "Setting light "
                + str(self.pixel_index)
                + " for "
                + self.airport_code
                + " "
                + self.metar_info.flightCategory
                + " "
                + str(self.color)
            )
            self.strip[self.pixel_index] = self.determine_brightness(self.color)
            await sleep(0)

def get_airport_codes():
    with open(os.path.join(os.getcwd(), 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()][:50]

AIRPORT_CODES = get_airport_codes()