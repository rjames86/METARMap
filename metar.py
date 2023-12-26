#  METARmaps.com
#  USA v1.81
#  OS v2.02

import urllib2
import xml.etree.ElementTree as ET
from neopixel import *

# LED strip configuration:
LED_COUNT = 249  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 12  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP = ws.WS2811_STRIP_GRB  # Strip type and colour ordering


strip = Adafruit_NeoPixel(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL,
    LED_STRIP,
)


strip.begin()


with open("/METARmaps/airports") as f:
    airports = f.readlines()
airports = [x.strip() for x in airports]
print(airports)


mydict = {"": ""}


url = "https://aviationweather.gov/cgi-bin/data/dataserver.php?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=1.5&stationString="
for airportcode in airports:
    if airportcode == "NULL":
        continue
    print(airportcode)
    url = url + airportcode + ","

print(url)
content = urllib2.urlopen(url).read()
print(content)


root = ET.fromstring(content)


for metar in root.iter("METAR"):
    if airportcode == "NULL":
        continue
    stationId = metar.find("station_id").text
    print(stationId)
    if metar.find("flight_category") is None:
        print("Skipping")
        continue

    flightCateory = metar.find("flight_category").text
    print(stationId + " " + flightCateory)
    if stationId in mydict:
        print("duplicate, only save first metar")
    else:
        mydict[stationId] = flightCateory

i = 0
for airportcode in airports:
    if airportcode == "NULL":
        i = i + 1
        continue
    print
    color = Color(0, 0, 0)

    flightCateory = mydict.get(airportcode, "No")
    print(airportcode + " " + flightCateory)

    GREEN = Color(255, 0, 0)
    BLUE = Color(0, 0, 255)
    RED = Color(0, 255, 0)
    PURPLE = Color(0, 128, 128)
    YELLOW = Color(255, 255, 0)
    WHITE = Color(255, 255, 255)

    FLIGHT_CATEGORY_TO_COLOR = {
        "VFR": YELLOW,
        "MVFR": BLUE,
        "IFR": RED,
        "LIFR": PURPLE,
    }

    if flightCateory != "No":
        color = FLIGHT_CATEGORY_TO_COLOR.get(
            flightCateory, WHITE
        )  # retuns either a color or None
    else:
        color = Color(255, 255, 255)
        print("N/A")

    print(
        "Setting light "
        + str(i)
        + " for "
        + airportcode
        + " "
        + flightCateory
        + " "
        + str(color)
    )
    strip.setPixelColor(i, color)
    strip.show()

    i = i + 1
print
print("fin")
