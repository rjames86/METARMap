import random
import asyncio

from constants import FLIGHT_CATEGORY_TO_COLOR, WHITE


class AirportLED:
    def __init__(self, strip, pixel_index, airport_code, metar_info):
        self.strip = strip
        self.pixel_index = pixel_index
        self.airport_code = airport_code
        self.metar_info = metar_info
    
    async def run(self):
        while True:
            print("running for ", self.airport_code)
            color = FLIGHT_CATEGORY_TO_COLOR.get(self.metar_info.flightCategory, WHITE)
            print(
                "Setting light "
                + str(self.pixel_index)
                + " for "
                + self.airport_code
                + " "
                + self.metar_info.flightCategory
                + " "
                + str(color)
            )
            self.strip.setPixelColor(self.pixel_index, color)


def get_airport_codes():
    with open(os.path.join(os.getcwd(), 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]
