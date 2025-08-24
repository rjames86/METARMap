import os
import time
from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE, WIND_BLINK_THRESHOLD

import astral
from astral.sun import sun as AstralSun

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
            self.sun = AstralSun(self.city.observer, tzinfo=self.city.tzinfo)
        self._color = BLACK

        self.generator = None

    def __repr__(self):
        return f"AirportLED<{self.airport_code}>"

    """
    Figure out how bright the light should be based on time of day
    """

    def determine_brightness(self, color):
        if self.city is None:
            return color

        G, R, B = color

        MIN_BRIGHTNESS = 0.01
        dimming_level = 1

        try:
            
            dawn = self.sun["dawn"]
            noon = self.sun["noon"]
            dusk = self.sun["dusk"]

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
            final_color = (G * dimming_level, R * dimming_level, B * dimming_level)
            if self.airport_code in ['KIAH', 'KDFW']:  # Debug first couple airports
                print(f"{self.airport_code}: dimming={dimming_level:.3f}, color={final_color}")
            return final_color
        except Exception as e:
            print(f"Brightness calculation error for {self.airport_code}: {e}")
            return color

    def fade_pixel(self, duration, index, new_color):
        start_color = self.strip[index]
        # G R B
        red_diff = new_color[1] - start_color[1]
        green_diff = new_color[0] - start_color[0]
        blue_diff = new_color[2] - start_color[2]

        delay = 0.01
        steps = int(duration // delay)
        for i in range(steps):
            red_value = start_color[1] + (red_diff * i // steps)
            green_value = start_color[0] + (green_diff * i // steps)
            blue_value = start_color[2] + (blue_diff * i // steps)
            yield (green_value, red_value, blue_value)

    def fade(self, color):
        current_color = color
        ALL_COLORS = [BLACK, color]
        while True:
            for color in ALL_COLORS:
                for next_color in  self.fade_pixel(0.1, self.pixel_index, current_color):
                    yield next_color
                current_color = color

    def get_color(self):
        if self.metar_info is None:
            return self._color
        if self.metar_info.flightCategory is None:
            return self._color

        new_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )

        new_color = self.determine_brightness(new_color)

        if self.metar_info.windGustSpeed >= WIND_BLINK_THRESHOLD:
            if self.generator is None:
                self.generator = self.fade(new_color)
        else:
            self.generator = None


        if self.generator:
            try:
                for next_color in self.generator:
                    return next_color
            except StopIteration:
                self.generator = None
                return new_color

        return new_color

    def set_pixel_color(self):
        self.strip[self.pixel_index] = self.get_color()
        

def get_airport_codes():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
