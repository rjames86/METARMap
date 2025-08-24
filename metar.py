from airports import AirportLED, AIRPORT_CODES
from constants import strip
from metar_data import get_metar_data
from logger import logger
import time

def run():
    logger.info("METARMap starting up...")
    now = time.time()

    try:
        metar_infos = get_metar_data()
        logger.info(f"Loaded weather data for {len(metar_infos)} airports")
        airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
        logger.info(f"Initialized {len(airport_leds)} LEDs")

        while True:
            if time.time() - now >= 60 * 5: # 5 minute
                logger.info("Updating weather data...")
                # Stop all animations before updating
                for led in airport_leds:
                    led.stop_animation()
                
                metar_infos = get_metar_data()
                logger.info(f"Updated weather data for {len(metar_infos)} airports")
                airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
                now = time.time()

            # Update static LEDs and start/stop animations as needed
            for airport_led in airport_leds:
                airport_led.set_pixel_color()
            strip.show()
            
            time.sleep(0.1)  # Reduce CPU usage since animations run in threads
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        # Stop all animations
        for led in airport_leds:
            led.stop_animation()
        # Turn off all LEDs
        strip.fill((0, 0, 0))
        strip.show()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    run()
