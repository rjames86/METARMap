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

        # Cache brightness factor — only needs to update every minute
        self._brightness_cache_value = None
        self._brightness_cache_time = None
        self._BRIGHTNESS_CACHE_SECONDS = 60

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
        import time as _time
        now_monotonic = _time.monotonic()
        if (self._brightness_cache_value is not None and
                self._brightness_cache_time is not None and
                now_monotonic - self._brightness_cache_time < self._BRIGHTNESS_CACHE_SECONDS):
            return self._brightness_cache_value

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

            # For locations where dusk falls after midnight UTC, astral returns the
            # previous night's dusk as today's — it will be earlier than dawn.
            # Add one day to get tonight's actual dusk.
            if dusk < dawn:
                dusk += datetime.timedelta(days=1)

            if current_time < dawn or current_time > dusk:
                result = MIN_BRIGHTNESS
            elif dawn < current_time < noon:
                total_seconds = noon - dawn
                seconds_until_noon = noon - current_time
                result = max(1 - (seconds_until_noon / total_seconds), MIN_BRIGHTNESS)
            elif noon < current_time < dusk:
                total_seconds = dusk - noon
                seconds_until_dusk = dusk - current_time
                result = max(seconds_until_dusk / total_seconds, MIN_BRIGHTNESS)
            else:
                result = 1.0

            self._brightness_cache_value = result
            self._brightness_cache_time = now_monotonic
            return result
        except Exception:
            return 1.0
    
    def apply_brightness_to_color(self, color, brightness_factor=None):
        """Apply brightness factor to a color tuple"""
        if brightness_factor is None:
            brightness_factor = self.calculate_brightness_factor()
        
        G, R, B = color
        return (G * brightness_factor, R * brightness_factor, B * brightness_factor)