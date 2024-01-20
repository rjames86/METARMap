import os

from constants import FLIGHT_CATEGORY_TO_COLOR, WHITE


class AirportLED:
    def __init__(self, strip, pixel_index, airport_code, metar_info):
        self.strip = strip
        self.pixel_index = pixel_index
        self.airport_code = airport_code
        self.metar_info = metar_info

    def __repr__(self):
        return f'AirportLED<{self.airport_code}>'
    
    async def run(self):
        try:
            while True:
                print("running for ", self.airport_code)
                if self.metar_info is None:
                    print("no metar info found for %s. Returning..." % self.airport_code)
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
                self.strip[self.pixel_index] = color
        except Exception as e:
            print(e)

def get_airport_codes():
    with open(os.path.join(os.getcwd(), 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]

AIRPORT_CODES = get_airport_codes()