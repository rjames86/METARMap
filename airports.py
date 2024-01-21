import os
from asyncio import sleep

from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE

import astral
from astral.sun import sun as AstralSun
import datetime
from logger import logger


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
            self.color = FLIGHT_CATEGORY_TO_COLOR.get(
                self.metar_info.flightCategory, WHITE
            )
            self.city = astral.LocationInfo(
                timezone="UTC",
                latitude=self.metar_info.latitude,
                longitude=self.metar_info.longitude,
            )

    def __repr__(self):
        return f"AirportLED<{self.airport_code}>"

    """
    Figure out how bright the light should be based on time of day
    """

    def determine_brightness(self, color):
        if self.city is None:
            return color

        G, R, B = color

        MIN_BRIGHTNESS = 0.1
        dimming_level = 1

        try:
            sun = AstralSun(self.city.observer, tzinfo=self.city.tzinfo)
            dawn = sun["dawn"]
            noon = sun["noon"]
            dusk = sun["dusk"]

            if (
                self.metar_info.observation_time < dawn
                or self.metar_info.observation_time > dusk
            ):
                dimming_level = MIN_BRIGHTNESS
            elif dawn < self.metar_info.observation_time < noon:
                total_seconds = noon - dawn
                seconds_until_noon = noon - self.metar_info.observation_time
                dimming_level = max(
                    1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS
                )
            elif noon < self.metar_info.observation_time < dusk:
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - self.metar_info.observation_time
                dimming_level = max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
            return (G * dimming_level, R * dimming_level, B * dimming_level)
        except Exception as e:
            logger.error(
                "Failed set brightness: %s %s" % (
                self.airport_code,
                self.metar_info.observation_time)
            )
            return color

    async def run(self):
        while True:
            logger.info("running for %s" % self.airport_code)
            if self.metar_info is None:
                logger.info(
                    "no metar info found for %s. Returning..." % self.airport_code
                )
                await sleep(0)
                return
            if self.metar_info.flightCategory is None:
                await sleep(0)
                return

            logger.info(
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
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "airports")) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
