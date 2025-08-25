import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airports import AirportLED, AIRPORT_CODES
from constants import get_strip
from metar_data import get_metar_data
from shared_logger import setup_logger
from startup_animation import startup_sequence
import time

logger = setup_logger('metarmap-led')

def run():
    logger.info("METARMap starting up...")
    now = time.time()

    try:
        strip = get_strip()
        
        # Run startup animation sequence
        startup_sequence(strip, logger)
        
        metar_infos = get_metar_data()
        logger.info(f"Loaded weather data for {len(metar_infos)} airports")
        airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
        logger.info(f"Initialized {len(airport_leds)} LEDs")

        while True:
            if time.time() - now >= 60 * 5: # 5 minute
                logger.info("Updating weather data...")
                metar_infos = get_metar_data()
                logger.info(f"Updated weather data for {len(metar_infos)} airports")
                airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
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
