import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from draw import OLEDDraw
from shared_logger import setup_logger

logger = setup_logger('metarmap-oled')

if __name__ == "__main__":
    logger.info("OLED Display starting up...")
    d = OLEDDraw()
    try:
        while True:
            d.write_screen()
    except KeyboardInterrupt:
        logger.info("Shutting down OLED display...")
        d.clear_screen()
        logger.info("OLED display shutdown complete")
    except Exception as e:
        logger.error(f"Unexpected error in OLED display: {e}")
        d.clear_screen()
        raise
