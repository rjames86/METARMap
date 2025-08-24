from airports import AirportLED, AIRPORT_CODES
from constants import strip
from metar_data import get_metar_data
import time

def run():
    now = time.time()

    metar_infos = get_metar_data()
    airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]

    while True:
        if time.time() - now >= 60 * 5: # 5 minute
            # Stop all animations before updating
            for led in airport_leds:
                led.stop_animation()
            
            metar_infos = get_metar_data()
            airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
            now = time.time()

        # Update static LEDs and start/stop animations as needed
        for airport_led in airport_leds:
            airport_led.set_pixel_color()
        strip.show()
        
        time.sleep(0.1)  # Reduce CPU usage since animations run in threads

if __name__ == "__main__":
    run()
