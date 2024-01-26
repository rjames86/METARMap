import neopixel
import board


# LED strip configuration:
LED_COUNT = 249  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 12  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
# LED_STRIP = ws.WS2811_STRIP_GRB  # Strip type and colour ordering

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
