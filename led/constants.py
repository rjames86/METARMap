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
ANIMATION_FRAME_DELAY = 0.03  # 33 FPS for smooth fades

def _detect_loop_delay():
    """Use a slower loop on Pi Zero W (single-core) to avoid pegging the CPU"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().lower()
        # Pi Zero 2 W contains both "zero 2" — only slow down the original Zero W
        if 'zero w' in model and 'zero 2' not in model:
            return 0.1  # ~10 FPS
    except Exception:
        pass
    return 0.05  # ~20 FPS

MAIN_LOOP_DELAY = _detect_loop_delay()

def get_strip():
    """Lazy-load the NeoPixel strip to avoid import issues during testing"""
    import neopixel
    import board
    
    LED_PIN = board.D18
    return neopixel.NeoPixel(
        LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False
    )
