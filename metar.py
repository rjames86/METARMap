from airports import AirportLED, AIRPORT_CODES
from constants import strip
from metar_data import get_metar_data
from time import sleep

def run():
    metar_infos = get_metar_data()
    print([(index, airport_code) for index, airport_code in enumerate(AIRPORT_CODES)])
    airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]

    while True:
        for airport_led in airport_leds:
            airport_led.set_pixel_color()
        strip.show()
        sleep(0.3)

if __name__ == "__main__":
    run()
