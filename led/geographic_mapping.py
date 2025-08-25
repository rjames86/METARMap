import math
import time
from typing import List, Tuple, Dict
from metar_data import get_metar_data
from airports import AIRPORT_CODES
from constants import BLACK, WHITE, GREEN


class GeographicMapper:
    def __init__(self):
        self.airport_positions = {}  # airport_code -> (lat, lon, led_index)
        self.led_to_position = {}    # led_index -> (lat, lon, airport_code)
        
    def build_mapping(self):
        """Fetch coordinates for all airports and build the mapping"""
        print("Fetching airport coordinates...")
        metar_data = get_metar_data()
        
        for led_index, airport_code in enumerate(AIRPORT_CODES):
            if airport_code in metar_data:
                metar_info = metar_data[airport_code]
                lat, lon = metar_info.latitude, metar_info.longitude
                
                self.airport_positions[airport_code] = (lat, lon, led_index)
                self.led_to_position[led_index] = (lat, lon, airport_code)
                print(f"{airport_code}: ({lat}, {lon}) -> LED {led_index}")
            else:
                print(f"Warning: No data for {airport_code}")
    
    def get_us_center(self) -> Tuple[float, float]:
        """Get approximate center of US for spiral calculations"""
        # Approximate geographic center of contiguous US
        return 39.8283, -98.5795
    
    def calculate_distance_from_center(self, lat: float, lon: float) -> float:
        """Calculate distance from US center using haversine formula"""
        center_lat, center_lon = self.get_us_center()
        
        # Convert to radians
        lat1, lon1 = math.radians(lat), math.radians(lon)
        lat2, lon2 = math.radians(center_lat), math.radians(center_lon)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in miles
        r = 3959
        return c * r
    
    def calculate_angle_from_center(self, lat: float, lon: float) -> float:
        """Calculate angle from US center (0 = north, increases clockwise)"""
        center_lat, center_lon = self.get_us_center()
        
        # Calculate angle using atan2
        dy = lat - center_lat
        dx = lon - center_lon
        
        # atan2 returns -π to π, convert to 0 to 2π with 0 = north
        angle = math.atan2(dx, dy)
        if angle < 0:
            angle += 2 * math.pi
            
        return angle
    
    def get_spiral_order(self, spiral_turns: float = 3.0) -> List[int]:
        """
        Get LEDs ordered for spiral animation from center outward.
        spiral_turns: How many times to spiral around (more = tighter spiral)
        """
        if not self.led_to_position:
            self.build_mapping()
        
        # Calculate spiral position for each LED
        spiral_positions = []
        
        for led_index, (lat, lon, airport_code) in self.led_to_position.items():
            distance = self.calculate_distance_from_center(lat, lon)
            angle = self.calculate_angle_from_center(lat, lon)
            
            # Create spiral: distance + angle offset creates spiral pattern
            spiral_pos = distance + (angle / (2 * math.pi)) * (distance / spiral_turns)
            spiral_positions.append((spiral_pos, led_index, airport_code))
        
        # Sort by spiral position
        spiral_positions.sort(key=lambda x: x[0])
        
        # Return just the LED indices in spiral order
        return [led_index for _, led_index, _ in spiral_positions]
    
    def get_geographic_regions(self) -> Dict[str, List[int]]:
        """Group LEDs by rough geographic regions"""
        if not self.led_to_position:
            self.build_mapping()
            
        regions = {
            'west_coast': [],
            'southwest': [],
            'mountain': [],
            'midwest': [],
            'south': [],
            'southeast': [],
            'northeast': [],
            'northwest': []
        }
        
        for led_index, (lat, lon, airport_code) in self.led_to_position.items():
            # Simple regional classification
            if lon < -115:  # West coast
                regions['west_coast'].append(led_index)
            elif lon < -105 and lat < 37:  # Southwest
                regions['southwest'].append(led_index)
            elif lon < -105 and lat >= 37:  # Mountain/Northwest
                if lat > 45:
                    regions['northwest'].append(led_index)
                else:
                    regions['mountain'].append(led_index)
            elif lon < -95:  # Midwest/West
                regions['midwest'].append(led_index)
            elif lat < 35:  # South
                regions['south'].append(led_index)
            elif lat < 40:  # Southeast
                regions['southeast'].append(led_index)
            else:  # Northeast
                regions['northeast'].append(led_index)
                
        return regions


def spiral_animation(strip, mapper: GeographicMapper, color=WHITE, wait_ms=30, fade_duration=500):
    """
    Animate LEDs in a spiral pattern from center of US outward.
    """
    print("Running geographic spiral animation...")
    
    # Get LEDs in spiral order
    spiral_order = mapper.get_spiral_order()
    
    # Clear strip
    strip.fill(BLACK)
    strip.show()
    
    # Light up LEDs in spiral order
    for i, led_index in enumerate(spiral_order):
        strip[led_index] = color
        strip.show()
        time.sleep(wait_ms / 1000.0)
    
    # Hold for a moment
    time.sleep(fade_duration / 1000.0)
    
    # Fade out in reverse order for cool effect
    for led_index in reversed(spiral_order):
        strip[led_index] = BLACK
        strip.show()
        time.sleep((wait_ms // 2) / 1000.0)


def regional_wave_animation(strip, mapper: GeographicMapper, wait_ms=300):
    """
    Light up regions in sequence like a wave across the country.
    """
    print("Running regional wave animation...")
    
    regions = mapper.get_geographic_regions()
    
    # Define wave order (west to east)
    wave_order = ['west_coast', 'southwest', 'mountain', 'northwest', 'midwest', 'south', 'southeast', 'northeast']
    colors = [WHITE, GREEN, WHITE, GREEN, WHITE, GREEN, WHITE, GREEN]  # Alternating colors
    
    strip.fill(BLACK)
    strip.show()
    
    for region_name, color in zip(wave_order, colors):
        if region_name in regions:
            # Light up this region
            for led_index in regions[region_name]:
                strip[led_index] = color
            strip.show()
            time.sleep(wait_ms / 1000.0)
    
    # Hold all lit
    time.sleep(500 / 1000.0)
    
    # Clear all
    strip.fill(BLACK)
    strip.show()


if __name__ == "__main__":
    # Test the geographic mapping
    mapper = GeographicMapper()
    mapper.build_mapping()
    
    print(f"\nMapped {len(mapper.led_to_position)} airports")
    
    # Show spiral order
    spiral_order = mapper.get_spiral_order()
    print(f"\nSpiral order (first 10): {spiral_order[:10]}")
    
    # Show regions
    regions = mapper.get_geographic_regions()
    for region, leds in regions.items():
        print(f"{region}: {len(leds)} airports")