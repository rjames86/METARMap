import os
from asyncio import sleep
import time

from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE, WIND_BLINK_THRESHOLD

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
                logger.info("Before dawn or after dusk")
                dimming_level = MIN_BRIGHTNESS
            elif dawn < self.metar_info.observation_time < noon:
                logger.info("After dawn and before noon")
                total_seconds = noon - dawn
                seconds_until_noon = noon - self.metar_info.observation_time
                dimming_level = max(
                    1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS
                )
            elif noon < self.metar_info.observation_time < dusk:
                logger.info("After noon and before dusk")
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - self.metar_info.observation_time
                dimming_level = max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
            logger.info("Dimming level set to %s" % dimming_level)
            return (G * dimming_level, R * dimming_level, B * dimming_level)
        except Exception as e:
            logger.error(
                "Failed set brightness: %s %s"
                % (self.airport_code, self.metar_info.observation_time)
            )
            return color

    def fade_pixel(self, duration, index, new_color):
        start_color = self.strip[index]
        # G R B
        red_diff = new_color[1] - start_color[1]
        green_diff = new_color[0] - start_color[0]
        blue_diff = new_color[2] - start_color[2]

        delay = 0.005
        steps = int(duration // delay)
        for i in range(steps):
            red_value = start_color[1] + (red_diff * i // steps)
            green_value = start_color[0] + (green_diff * i // steps)
            blue_value = start_color[2] + (blue_diff * i // steps)

            self.strip[index] = (green_value, red_value, blue_value)
            # self.strip.show()
            time.sleep(delay)

    async def fade(self):
        logger.info("Fading %s. Index %s" % (self.airport_code, self.pixel_index))
        current_color = self.color
        # G, R, B = self.color
        # ALL_COLORS = [(G * 0.5, R * 0.5, B * 0.5) , self.color]
        ALL_COLORS = [BLACK , self.color]
        while True:
            logger.info("while true %s" % self.airport_code)
            for color in ALL_COLORS:
                self.fade_pixel(0.3, self.pixel_index, current_color)
                current_color = color
                await sleep(0)

    async def run(self):
        logger.info("running for %s" % self.airport_code)
        if self.metar_info is None:
            logger.info("no metar info found for %s. Returning..." % self.airport_code)
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

        if self.metar_info.windSpeed >= WIND_BLINK_THRESHOLD:
            await self.fade()
            await sleep(0)
        else:
            self.strip[self.pixel_index] = self.determine_brightness(self.color)
            await sleep(0)


def get_airport_codes():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "airports")) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
