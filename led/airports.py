import os
import time
from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE, WIND_BLINK_THRESHOLD
from sun_calculator import SunCalculator

class AirportLED:
    def __init__(self, strip, pixel_index, airport_code, metar_info):
        self.strip = strip
        self.pixel_index = pixel_index
        self.airport_code = airport_code
        self.metar_info = metar_info

        if self.metar_info is None:
            self.sun_calculator = None
        else:
            self.sun_calculator = SunCalculator(
                self.metar_info.latitude,
                self.metar_info.longitude
            )
        self._color = BLACK

        # Fade state tracking
        self.should_fade = False
        self.fade_start_time = 0
        self.fade_duration = 2.0  # seconds for each fade direction
        self.fade_direction = 1  # 1 = fading to black, -1 = fading to color

    def __repr__(self):
        return f"AirportLED<{self.airport_code}>"

    def determine_brightness(self, color):
        """Apply brightness dimming based on time of day"""
        if self.sun_calculator is None:
            return color
        
        return self.sun_calculator.apply_brightness_to_color(color)

    def calculate_fade_color(self, base_color, current_time):
        if not self.should_fade:
            return base_color
            
        elapsed = current_time - self.fade_start_time
        
        # Check if we need to switch direction
        if elapsed >= self.fade_duration:
            self.fade_direction *= -1  # Flip direction
            self.fade_start_time = current_time
            elapsed = 0
        
        # Calculate fade progress (0 to 1)
        progress = elapsed / self.fade_duration
        
        if self.fade_direction == 1:
            # Fading from base_color to black
            start_color = base_color
            end_color = BLACK
        else:
            # Fading from black to base_color
            start_color = BLACK
            end_color = base_color
        
        # Interpolate between colors
        red_value = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
        green_value = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
        blue_value = int(start_color[2] + (end_color[2] - start_color[2]) * progress)
        
        return (green_value, red_value, blue_value)

    def get_color(self):
        if self.metar_info is None:
            return self._color
        if self.metar_info.flightCategory is None:
            return self._color

        base_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )
        base_color = self.determine_brightness(base_color)

        should_fade = self.metar_info.windGustSpeed >= WIND_BLINK_THRESHOLD
        
        # Start or stop fading based on wind conditions
        if should_fade and not self.should_fade:
            self.should_fade = True
            self.fade_start_time = time.time()
            self.fade_direction = 1
        elif not should_fade:
            self.should_fade = False
        
        # Calculate the current color (static or fading)
        return self.calculate_fade_color(base_color, time.time())
    
    def get_static_color(self):
        if self.metar_info is None:
            return self._color
        if self.metar_info.flightCategory is None:
            return self._color

        new_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )
        return self.determine_brightness(new_color)

    def set_pixel_color(self):
        self.strip[self.pixel_index] = self.get_color()
        

def get_airport_codes():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
