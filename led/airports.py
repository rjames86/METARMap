import os
import time
import datetime
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

        # Fade state tracking
        self.should_fade = False
        self.fade_start_time = 0
        self.fade_duration = 2.0  # seconds for each fade direction
        self.fade_direction = 1  # 1 = fading to black, -1 = fading to color
        
        # Cache sun times to avoid recalculating every frame
        self._cached_sun_times = None
        self._cached_date = None

    def __repr__(self):
        return f"AirportLED<{self.airport_code}>"

    @property
    def sun_times(self):
        """Get sun times for the observation date, cached to avoid recalculation every frame"""
        if self.metar_info is None or self.city is None:
            return None
            
        obs_date = self.metar_info.observation_time.date()
        
        # Cache sun times to avoid expensive recalculation every frame
        if self._cached_date != obs_date or self._cached_sun_times is None:
            print(f"DEBUG: {self.airport_code} calculating sun times for date {obs_date} at lat/lon {self.city.latitude}/{self.city.longitude}")
            self._cached_sun_times = AstralSun(self.city.observer, date=obs_date, tzinfo=self.city.tzinfo)
            self._cached_date = obs_date
            print(f"DEBUG: {self.airport_code} calculated dawn: {self._cached_sun_times['dawn']}")
            
        return self._cached_sun_times

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
            # Use current time for brightness, not historical observation time
            current_time = datetime.datetime.now(datetime.timezone.utc)
            current_date = current_time.date()
            
            # Calculate sun times for current date, not observation date
            sun_times = AstralSun(self.city.observer, date=current_date, tzinfo=self.city.tzinfo)
            
            dawn = sun_times["dawn"]
            noon = sun_times["noon"] 
            dusk = sun_times["dusk"]
            
            print(f"DEBUG: {self.airport_code} - current:{current_time}, dawn:{dawn}, noon:{noon}, dusk:{dusk}")

            if (
                current_time < dawn
                or current_time > dusk
            ):
                dimming_level = MIN_BRIGHTNESS
                print(f"DEBUG: {self.airport_code} - NIGHT TIME, dimming to {MIN_BRIGHTNESS}")
            elif dawn < current_time < noon:
                total_seconds = noon - dawn
                seconds_until_noon = noon - current_time
                dimming_level = max(
                    1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS
                )
                print(f"DEBUG: {self.airport_code} - MORNING, dimming to {dimming_level}")
            elif noon < current_time < dusk:
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - current_time
                dimming_level = max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
                print(f"DEBUG: {self.airport_code} - AFTERNOON, dimming to {dimming_level}")
            else:
                print(f"DEBUG: {self.airport_code} - DAY TIME, no dimming")
                
            final_color = (G * dimming_level, R * dimming_level, B * dimming_level)
            print(f"DEBUG: {self.airport_code} - original color: {color}, dimmed: {final_color}")
            return final_color
        except Exception as e:
            return color

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
