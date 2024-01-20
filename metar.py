import asyncio
from airports import AirportLED
from constants import strip
from metar_data import get_metar_data

async def run():
    metar_infos = get_metar_data()
    airport_leds = [AirportLED(strip, index, airport_code, metar_infos[airport_code]) for index, airport_code in enumerate(metar_infos.keys())]
    print(airport_leds)
    tasks = [airport_led.run() for airport_led in airport_leds]
    results = asyncio.gather(*tasks)
    try:
        await results
    except Exception as e:
        print(e)
        print("Cancelling")
        results.cancel()


try:
    asyncio.run(run())
except Exception as e:
    print(e)
    pass
