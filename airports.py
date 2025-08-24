import os
import time
import threading
from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE, WIND_BLINK_THRESHOLD, ANIMATION_FRAME_DELAY

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
        self.thread = None
        self.running = False
        self.lock = threading.Lock()
        self.fade_speed = 2.0  # Default fade duration (longer = smoother)
        self.blink_speed = 0.5  # Default blink cycle time

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
            return (G * dimming_level, R * dimming_level, B * dimming_level)
        except Exception as e:
            return color

    def fade_pixel(self, duration, start_color, end_color):
        # G R B
        red_diff = end_color[1] - start_color[1]
        green_diff = end_color[0] - start_color[0]
        blue_diff = end_color[2] - start_color[2]

        delay = ANIMATION_FRAME_DELAY
        steps = max(1, int(duration / delay))  # Use / instead of // for more steps
        for i in range(steps + 1):  # Include the final step
            progress = i / steps if steps > 0 else 1.0
            red_value = int(start_color[1] + (red_diff * progress))
            green_value = int(start_color[0] + (green_diff * progress))
            blue_value = int(start_color[2] + (blue_diff * progress))
            yield (green_value, red_value, blue_value)

    def fade(self, target_color):
        while True:
            # Fade from target to black
            for next_color in self.fade_pixel(self.fade_speed, target_color, BLACK):
                yield next_color
            # Fade from black to target immediately (no hold)
            for next_color in self.fade_pixel(self.fade_speed, BLACK, target_color):
                yield next_color

    def get_color(self):
        if self.metar_info is None:
            return self._color
        if self.metar_info.flightCategory is None:
            return self._color

        new_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )

        new_color = self.determine_brightness(new_color)

        should_animate = self.metar_info.windGustSpeed >= WIND_BLINK_THRESHOLD
        
        if should_animate and not self.running:
            self.generator = self.fade(new_color)
            self.start_animation()
        elif not should_animate and self.running:
            self.stop_animation()
        elif should_animate and self.generator is None:
            self.generator = self.fade(new_color)


        if self.generator:
            try:
                return next(self.generator)
            except StopIteration:
                self.generator = self.fade(new_color)
                return next(self.generator)

        return new_color
    
    def get_static_color(self):
        if self.metar_info is None:
            return self._color
        if self.metar_info.flightCategory is None:
            return self._color

        new_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )
        return self.determine_brightness(new_color)

    def _animation_loop(self):
        while self.running:
            if self.generator:
                try:
                    color = next(self.generator)
                    with self.lock:
                        self.strip[self.pixel_index] = color
                except StopIteration:
                    with self.lock:
                        self.generator = None
                        self.strip[self.pixel_index] = self.get_static_color()
            time.sleep(ANIMATION_FRAME_DELAY)
    
    def start_animation(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.thread.start()
    
    def stop_animation(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None

    def set_pixel_color(self):
        if not self.running:
            with self.lock:
                self.strip[self.pixel_index] = self.get_color()
        

def get_airport_codes():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
