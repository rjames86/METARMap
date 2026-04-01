import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airports import AirportLED, AIRPORT_CODES
from constants import get_strip, MAIN_LOOP_DELAY
from metar_data import get_metar_data
from shared_logger import setup_logger
from startup_animation import startup_sequence
import time

logger = setup_logger('metarmap-led')

_BOOT_FLAG = '/run/metarmap_started'

def _is_first_start():
    """Returns True on the first start after a reboot, False on crash restarts."""
    if os.path.exists(_BOOT_FLAG):
        return False
    open(_BOOT_FLAG, 'w').close()
    return True

def run():
    logger.info("METARMap starting up...")
    now = time.time()

    try:
        strip = get_strip()

        if _is_first_start():
            logger.info("First start after boot — running startup animation.")
            startup_sequence(strip, logger)
        else:
            logger.info("Restarting after failure — skipping startup animation.")
        
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
            
            time.sleep(MAIN_LOOP_DELAY)
            
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
