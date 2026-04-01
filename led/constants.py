# LED strip configuration:
LED_COUNT = 249
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

# Animation timing
# Increase this on slower hardware (e.g. 0.1 for Pi Zero W, 0.05 for Pi Zero 2 W+)
ANIMATION_FRAME_DELAY = 0.03  # 33 FPS for smooth fades
MAIN_LOOP_DELAY = 0.05  # seconds between LED updates (~20 FPS)

def get_strip():
    """Lazy-load the NeoPixel strip to avoid import issues during testing"""
    import neopixel
    import board
    
    LED_PIN = board.D18
    return neopixel.NeoPixel(
        LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False
    )
