import asyncio
from airports import AirportLED, AIRPORT_CODES
from constants import strip
from metar_data import get_metar_data

async def run():
    metar_infos = get_metar_data()
    print([(index, airport_code) for index, airport_code in enumerate(AIRPORT_CODES)])
    airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
    print(airport_leds)
    tasks = [airport_led.run() for airport_led in airport_leds]
    results = asyncio.gather(*tasks)
    try:
        await results
    except Exception as e:
        print("Cancelling")
        print(e)
        results.cancel()


try:
    print("Starting...")
    asyncio.run(run())
except Exception as e:
    print(e)
    pass
