import os
import time
from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE, WIND_BLINK_THRESHOLD

import astral
from astral.sun import sun as AstralSun
from logger import logger


class AirportLED:
    def __init__(self, strip, pixel_index, airport_code, metar_info):
        self.strip = strip
        self.pixel_index = pixel_index
        self.airport_code = airport_code
        self.metar_info = metar_info

        if self.metar_info is None:
            self.city = None
        else:
            self.city = astral.LocationInfo(
                timezone="UTC",
                latitude=self.metar_info.latitude,
                longitude=self.metar_info.longitude,
            )
        self._color = BLACK
    def __repr__(self):
        return f"AirportLED<{self.airport_code}>"

    """
    Figure out how bright the light should be based on time of day
    """

    def determine_brightness(self, color):
        if self.city is None:
            return color

        G, R, B = color

        MIN_BRIGHTNESS = 0.05
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
                # logger.info("Before dawn or after dusk")
                dimming_level = MIN_BRIGHTNESS
            elif dawn < self.metar_info.observation_time < noon:
                # logger.info("After dawn and before noon")
                total_seconds = noon - dawn
                seconds_until_noon = noon - self.metar_info.observation_time
                dimming_level = max(
                    1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS
                )
            elif noon < self.metar_info.observation_time < dusk:
                # logger.info("After noon and before dusk")
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - self.metar_info.observation_time
                dimming_level = max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
            # logger.info("Dimming level set to %s" % dimming_level)
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
            logger.info("Fading %s from %s to %s" % (self.airport_code, str(new_color), str((green_value, red_value, blue_value))))
            yield (green_value, red_value, blue_value)

    def fade(self, color):
        logger.info("Fading %s. Index %s" % (self.airport_code, self.pixel_index))
        current_color = color
        # G, R, B = self.color
        # ALL_COLORS = [(G * 0.5, R * 0.5, B * 0.5) , self.color]
        ALL_COLORS = [BLACK, color]
        while True:
            for color in ALL_COLORS:
                next_color = self.fade_pixel(0.3, self.pixel_index, current_color)
                current_color = color
                return next_color

    @property
    def color(self):
        if self.metar_info is None:
            # logger.info("no metar info found for %s. Returning..." % self.airport_code)
            return self._color
        if self.metar_info.flightCategory is None:
            return self._color

        new_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )

        new_color = self.determine_brightness(new_color)

        if self.metar_info.windSpeed >= WIND_BLINK_THRESHOLD:
            new_color = next(self.fade(new_color))

        self._color = new_color

        logger.info(
            "Setting light "
            + str(self.pixel_index)
            + " for "
            + self.airport_code
            + " "
            + self.metar_info.flightCategory
            + " "
            + str(self._color)
        )

        return self._color


    def set_pixel_color(self):
        self.strip[self.pixel_index] = self.color
        

def get_airport_codes():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "airports")) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
