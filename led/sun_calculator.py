import datetime
import astral
from astral.sun import sun as AstralSun


class SunCalculator:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.city = astral.LocationInfo(
            timezone="UTC",
            latitude=self.latitude,
            longitude=self.longitude,
        )
        
        # Cache sun times to avoid recalculating every frame
        self._cached_sun_times = None
        self._cached_date = None
        self._cached_current_sun_times = None
        self._cached_current_date = None

    def get_sun_times_for_date(self, date):
        """Get sun times for a specific date, cached to avoid recalculation every frame"""
        if self._cached_date != date or self._cached_sun_times is None:
            self._cached_sun_times = AstralSun(self.city.observer, date=date, tzinfo=self.city.tzinfo)
            self._cached_date = date
        return self._cached_sun_times
    
    def get_current_sun_times(self):
        """Get sun times for current date, cached to avoid recalculation every frame"""
        # Use current time for brightness, not historical observation time
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Get local time at airport to determine correct date
        # Rough estimate: longitude degrees * 4 minutes = timezone offset
        timezone_offset_hours = self.longitude / 15  # 15 degrees per hour
        local_time = current_time + datetime.timedelta(hours=timezone_offset_hours)
        local_date = local_time.date()
        
        # Cache sun times for current date to avoid expensive recalculation every frame
        if self._cached_current_date != local_date or self._cached_current_sun_times is None:
            self._cached_current_sun_times = AstralSun(self.city.observer, date=local_date, tzinfo=self.city.tzinfo)
            self._cached_current_date = local_date
        
        return self._cached_current_sun_times
    
    def calculate_brightness_factor(self, current_time=None):
        """Calculate brightness dimming factor based on time of day (0.01 to 1.0)"""
        if current_time is None:
            current_time = datetime.datetime.now(datetime.timezone.utc)
        
        MIN_BRIGHTNESS = 0.01
        
        try:
            sun_times = self.get_current_sun_times()
            if sun_times is None:
                return 1.0
            
            dawn = sun_times["dawn"]
            noon = sun_times["noon"] 
            dusk = sun_times["dusk"]

            if current_time < dawn or current_time > dusk:
                return MIN_BRIGHTNESS
            elif dawn < current_time < noon:
                total_seconds = noon - dawn
                seconds_until_noon = noon - current_time
                return max(1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS)
            elif noon < current_time < dusk:
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - current_time
                return max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
            else:
                return 1.0
        except Exception:
            return 1.0
    
    def apply_brightness_to_color(self, color, brightness_factor=None):
        """Apply brightness factor to a color tuple"""
        if brightness_factor is None:
            brightness_factor = self.calculate_brightness_factor()
        
        G, R, B = color
        return (G * brightness_factor, R * brightness_factor, B * brightness_factor)