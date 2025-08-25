import os
import time
import logging
from constants import BLACK, FLIGHT_CATEGORY_TO_COLOR, WHITE, WIND_BLINK_THRESHOLD

import astral
from astral.sun import sun as AstralSun

logger = logging.getLogger(__name__)
# Set debug level for color debugging
logger.setLevel(logging.DEBUG)

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

    def __repr__(self):
        return f"AirportLED<{self.airport_code}>"

    """
    Figure out how bright the light should be based on time of day
    """

    def determine_brightness(self, color):
        logger.debug(f"{self.airport_code}: Determining brightness for color {color}")
        
        if self.city is None:
            logger.debug(f"{self.airport_code}: No city info, using full brightness")
            return color

        G, R, B = color

        MIN_BRIGHTNESS = 0.01
        dimming_level = 1

        try:
            obs_time = self.metar_info.observation_time
            
            # Calculate sun times for the specific date of the observation
            obs_date = obs_time.date()
            sun_times = AstralSun(self.city.observer, date=obs_date, tzinfo=self.city.tzinfo)
            
            dawn = sun_times["dawn"]
            noon = sun_times["noon"] 
            dusk = sun_times["dusk"]
            
            logger.debug(f"{self.airport_code}: Times - dawn: {dawn}, noon: {noon}, dusk: {dusk}, obs: {obs_time}")

            if (
                obs_time < dawn
                or obs_time > dusk
            ):
                dimming_level = MIN_BRIGHTNESS
                logger.debug(f"{self.airport_code}: Night time, dimming to {MIN_BRIGHTNESS}")
            elif dawn < obs_time < noon:
                total_seconds = noon - dawn
                seconds_until_noon = noon - obs_time
                dimming_level = max(
                    1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS
                )
                logger.debug(f"{self.airport_code}: Morning, dimming to {dimming_level}")
            elif noon < obs_time < dusk:
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - obs_time
                dimming_level = max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
                logger.debug(f"{self.airport_code}: Afternoon, dimming to {dimming_level}")
            else:
                logger.debug(f"{self.airport_code}: Day time, full brightness")
                
            final_color = (G * dimming_level, R * dimming_level, B * dimming_level)
            logger.debug(f"{self.airport_code}: Brightness adjusted color: {final_color}")
            return final_color
        except Exception as e:
            logger.error(f"{self.airport_code}: Error in brightness calculation: {e}")
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
        logger.debug(f"{self.airport_code}: Getting color...")
        
        if self.metar_info is None:
            logger.debug(f"{self.airport_code}: No METAR info, returning BLACK")
            return self._color
            
        if self.metar_info.flightCategory is None:
            logger.debug(f"{self.airport_code}: No flight category, returning BLACK")
            return self._color

        logger.debug(f"{self.airport_code}: Flight category = {self.metar_info.flightCategory}")
        
        base_color = FLIGHT_CATEGORY_TO_COLOR.get(
            self.metar_info.flightCategory, WHITE
        )
        logger.debug(f"{self.airport_code}: Base color from flight category = {base_color}")
        
        base_color = self.determine_brightness(base_color)
        logger.debug(f"{self.airport_code}: Color after brightness adjustment = {base_color}")

        should_fade = self.metar_info.windGustSpeed >= WIND_BLINK_THRESHOLD
        logger.debug(f"{self.airport_code}: Wind gust speed = {self.metar_info.windGustSpeed}, threshold = {WIND_BLINK_THRESHOLD}, should_fade = {should_fade}")
        
        # Start or stop fading based on wind conditions
        if should_fade and not self.should_fade:
            self.should_fade = True
            self.fade_start_time = time.time()
            self.fade_direction = 1
            logger.debug(f"{self.airport_code}: Started fading due to wind gusts")
        elif not should_fade:
            self.should_fade = False
        
        # Calculate the current color (static or fading)
        final_color = self.calculate_fade_color(base_color, time.time())
        logger.debug(f"{self.airport_code}: Final color = {final_color}")
        return final_color
    
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
        color = self.get_color()
        logger.debug(f"{self.airport_code}: Setting LED[{self.pixel_index}] to color {color}")
        self.strip[self.pixel_index] = color
        

def get_airport_codes():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]


AIRPORT_CODES = get_airport_codes()
