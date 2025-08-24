import time

import adafruit_ssd1306
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont

from airport import AirportData
from config import (
    CYCLE_TIME,
    SMALL_FONT_SIZE,
    LARGE_FONT_SIZE,
    DISPLAY_VALUES,
)

SCROLL_DELAY = 0.001  # Much faster scrolling


class OLEDDraw:
    def __init__(self):
        self.width = 128
        self.height = 64
        self.border = 5

        self.padding = 0
        self.top = self.padding
        self.bottom = self.height - self.padding

        i2c = board.I2C()
        self.oled = adafruit_ssd1306.SSD1306_I2C(
            self.width,
            self.height,
            i2c,
            addr=0x3C,
        )

        self.oled.fill(0)
        self.oled.show()

        self.cycle_time = CYCLE_TIME

        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        try:
            # Try common Raspberry Pi font paths
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", SMALL_FONT_SIZE)
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", LARGE_FONT_SIZE)
        except OSError:
            try:
                # Alternative font path
                self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", SMALL_FONT_SIZE)
                self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", LARGE_FONT_SIZE)
            except OSError:
                # Fall back to default font
                self.font_small = ImageFont.load_default()
                self.font_large = ImageFont.load_default()

        self.ad = AirportData()

    def wait(self, wait):
        time.sleep(wait)

    def draw_header(self, position, text):
        self.draw.text((position, self.top), text, font=self.font_small, fill=255)

    def draw_body(self, position, text):
        self.draw.text(position, text, font=self.font_large, fill=255)

    def show(self, wait):
        self.oled.image(self.image)
        self.oled.show()
        self.wait(wait)

    def scroll_text(self, display_text, header):
        x = 0
        width, _ = self.font_large.getsize(display_text)
        # Start at negative half the screen so that the scrolling text starts at the middle of the screen
        for i in range(0, (width - self.width) + self.border, 2):
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            self.draw_header(0, header)
            self.draw_body((x - i, self.top + 12), display_text)
            if i == 0:
                self.show(1)
            else:
                self.show(SCROLL_DELAY)
        self.wait(1)

    def clear_screen(self):
        self.oled.fill(0)
        self.oled.show()

    def write_screen(self):
        print("Writing screen...")
        self.ad.should_refresh()
        x = 0

        for key in DISPLAY_VALUES:
            display_text = self.ad[key]
            if display_text is None:
                print("%s is None. Skipping..." % key)
                continue

            header = "%s - %s" % (self.ad.station_id, self.ad.READABLE_NAMES[key])

            print("Writing: %s - %s" % (header, display_text))

            width, _ = self.font_large.getsize(display_text)
            if width > self.width:
                self.scroll_text(display_text, header)
            else:
                self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
                self.draw_header(x + self.padding, header)
                self.draw_body((x + self.padding, self.top + 12), display_text)
                # self.image.show()
                self.show(self.cycle_time)
