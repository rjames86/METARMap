#!/usr/bin/env python3
"""
Test script for geographic mapping functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geographic_mapping import GeographicMapper


def test_geographic_mapping():
    """Test the geographic mapping system"""
    print("Testing Geographic Mapping System")
    print("=" * 40)
    
    mapper = GeographicMapper()
    
    try:
        # This will fetch real METAR data
        print("Fetching airport coordinates from METAR API...")
        mapper.build_mapping()
        
        print(f"\nSuccessfully mapped {len(mapper.led_to_position)} airports")
        
        # Show some examples
        print("\nFirst 10 airports with coordinates:")
        for i, (lat, lon, airport_code) in list(mapper.led_to_position.items())[:10]:
            print(f"  LED {i:3d}: {airport_code} at ({lat:6.2f}, {lon:7.2f})")
        
        # Test spiral ordering
        print("\nCalculating spiral order...")
        spiral_order = mapper.get_spiral_order()
        print(f"Spiral order calculated for {len(spiral_order)} airports")
        
        # Show first 10 in spiral order
        print("First 10 airports in spiral order:")
        for i, led_index in enumerate(spiral_order[:10]):
            lat, lon, airport_code = mapper.led_to_position[led_index]
            distance = mapper.calculate_distance_from_center(lat, lon)
            print(f"  {i+1:2d}. LED {led_index:3d}: {airport_code} ({distance:4.0f} miles from center)")
        
        # Test regional grouping
        print("\nRegional groupings:")
        regions = mapper.get_geographic_regions()
        for region_name, led_indices in regions.items():
            if led_indices:
                print(f"  {region_name:12s}: {len(led_indices):2d} airports")
                # Show a few examples
                examples = []
                for led_index in led_indices[:3]:
                    _, _, airport_code = mapper.led_to_position[led_index]
                    examples.append(airport_code)
                if examples:
                    print(f"                   Examples: {', '.join(examples)}")
        
        print("\n✅ Geographic mapping test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Geographic mapping test failed: {e}")
        return False


if __name__ == "__main__":
    test_geographic_mapping()