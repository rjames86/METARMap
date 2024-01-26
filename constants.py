import neopixel
import board


# LED strip configuration:
LED_COUNT = 249
LED_PIN = board.D18 
LED_BRIGHTNESS = 12  # Set to 0 for darkest and 255 for brightest

BLACK = (0, 0, 0)
GREEN = (255, 0, 0)
BLUE = (0, 0, 255)
RED = (0, 255, 0)
PURPLE = (0, 128, 128)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

FLIGHT_CATEGORY_TO_COLOR = {
    "VFR": GREEN,
    "MVFR": BLUE,
    "IFR": RED,
    "LIFR": PURPLE,
}

WIND_BLINK_THRESHOLD = 10

strip = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False
)
