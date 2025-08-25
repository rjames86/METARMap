import time
import math
from constants import LED_COUNT, BLACK, GREEN, BLUE, RED, PURPLE, YELLOW, WHITE


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


def rainbow_cycle(strip, wait_ms=20, iterations=3):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(LED_COUNT):
            strip[i] = wheel(((i * 256 // LED_COUNT) + j) & 255)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def color_wipe(strip, color, wait_ms=10):
    """Wipe color across display a pixel at a time."""
    for i in range(LED_COUNT):
        strip[i] = color
        strip.show()
        time.sleep(wait_ms / 1000.0)


def theater_chase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, LED_COUNT, 3):
                if i + q < LED_COUNT:
                    strip[i + q] = color
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, LED_COUNT, 3):
                if i + q < LED_COUNT:
                    strip[i + q] = BLACK


def fade_in_out(strip, color, wait_ms=5, steps=50):
    """Fade all pixels in and out with a color."""
    # Fade in
    for brightness in range(steps):
        factor = brightness / steps
        faded_color = tuple(int(c * factor) for c in color)
        strip.fill(faded_color)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    
    # Fade out
    for brightness in range(steps, 0, -1):
        factor = brightness / steps
        faded_color = tuple(int(c * factor) for c in color)
        strip.fill(faded_color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def breathing_effect(strip, color, wait_ms=10, cycles=3):
    """Breathing effect using sine wave."""
    for cycle in range(cycles):
        for i in range(314):  # Roughly 2*pi*50 for smooth sine wave
            brightness = (math.sin(i / 50.0) + 1) / 2  # 0 to 1
            faded_color = tuple(int(c * brightness) for c in color)
            strip.fill(faded_color)
            strip.show()
            time.sleep(wait_ms / 1000.0)


def runway_lights(strip, wait_ms=50, iterations=3):
    """Airport runway-style sequential lighting."""
    colors = [WHITE, YELLOW, WHITE, YELLOW]
    
    for iteration in range(iterations):
        # Light up sections sequentially
        section_size = LED_COUNT // 8
        for section in range(8):
            start = section * section_size
            end = min((section + 1) * section_size, LED_COUNT)
            color = colors[section % len(colors)]
            
            for i in range(start, end):
                strip[i] = color
            strip.show()
            time.sleep(wait_ms / 1000.0)
        
        # Clear all
        strip.fill(BLACK)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def flight_category_demo(strip, wait_ms=500):
    """Demo each flight category color."""
    from constants import FLIGHT_CATEGORY_TO_COLOR
    
    categories = ["VFR", "MVFR", "IFR", "LIFR"]
    
    for category in categories:
        color = FLIGHT_CATEGORY_TO_COLOR[category]
        strip.fill(color)
        strip.show()
        time.sleep(wait_ms / 1000.0)
    
    # Clear
    strip.fill(BLACK)
    strip.show()


def startup_sequence(strip, logger=None):
    """Run a complete startup animation sequence."""
    if logger:
        logger.info("Starting LED startup animation sequence...")
    
    # Clear strip
    strip.fill(BLACK)
    strip.show()
    
    # 1. Brief flash to show all LEDs work
    if logger:
        logger.info("LED test flash...")
    strip.fill(WHITE)
    strip.show()
    time.sleep(0.2)
    strip.fill(BLACK)
    strip.show()
    time.sleep(0.3)
    
    # 2. Rainbow cycle
    if logger:
        logger.info("Rainbow cycle animation...")
    rainbow_cycle(strip, wait_ms=15, iterations=2)
    
    # 3. Flight category demo
    if logger:
        logger.info("Flight category color demo...")
    flight_category_demo(strip, wait_ms=600)
    
    # 4. Breathing effect with green
    if logger:
        logger.info("Breathing effect...")
    breathing_effect(strip, GREEN, wait_ms=8, cycles=2)
    
    # 5. Runway lights effect
    if logger:
        logger.info("Runway lights effect...")
    runway_lights(strip, wait_ms=80, iterations=2)
    
    # Final clear
    strip.fill(BLACK)
    strip.show()
    
    if logger:
        logger.info("Startup animation sequence complete!")


if __name__ == "__main__":
    # Test the animations
    from constants import get_strip
    
    strip = get_strip()
    print("Running startup animation test...")
    startup_sequence(strip)
    print("Animation complete!")