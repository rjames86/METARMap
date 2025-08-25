import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airports import AirportLED, AIRPORT_CODES
from constants import get_strip
from metar_data import get_metar_data
from shared_logger import setup_logger
import time

logger = setup_logger('metarmap-led')

def run():
    logger.info("METARMap starting up...")
    now = time.time()

    try:
        strip = get_strip()
        metar_infos = get_metar_data()
        logger.info(f"Loaded weather data for {len(metar_infos)} airports")
        airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
        logger.info(f"Initialized {len(airport_leds)} LEDs")

        while True:
            if time.time() - now >= 60 * 1: # 1 minute for debugging
                logger.info("Updating weather data...")
                metar_infos = get_metar_data()
                logger.info(f"Updated weather data for {len(metar_infos)} airports")
                
                # Debug: Check a few airports before recreating LEDs
                test_airports = ['KSLC', 'KIAH', 'KDFW']
                for airport in test_airports:
                    if airport in metar_infos:
                        info = metar_infos[airport]
                        logger.info(f"DEBUG: {airport} has data - {info.flightCategory}, temp: {info.tempC}°C")
                    else:
                        logger.warning(f"DEBUG: {airport} missing from updated data")
                
                airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
                
                # Debug: Check LED creation
                leds_with_data = sum(1 for led in airport_leds if led.metar_info is not None)
                logger.info(f"DEBUG: Created {len(airport_leds)} LEDs, {leds_with_data} have data, {len(airport_leds) - leds_with_data} have no data")
                
                now = time.time()

            # Update all LEDs (static and fading)
            for airport_led in airport_leds:
                airport_led.set_pixel_color()
            strip.show()
            
            time.sleep(0.05)  # ~20 FPS for smooth fades
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        # Turn off all LEDs
        strip.fill((0, 0, 0))
        strip.show()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    run()
