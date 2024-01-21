import asyncio
from airports import AirportLED, AIRPORT_CODES
from constants import strip
from metar_data import get_metar_data

async def run():
    loop = asyncio.get_event_loop()
    metar_infos = get_metar_data()
    print([(index, airport_code) for index, airport_code in enumerate(AIRPORT_CODES)])
    airport_leds = [AirportLED(strip, index, airport_code, metar_infos.get(airport_code)) for index, airport_code in enumerate(AIRPORT_CODES)]
    print(airport_leds)
    tasks = [loop.create_task(airport_led.run()) for airport_led in airport_leds]
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print("Cancelling")
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks)
        raise e

print("Starting...")
# asyncio.run(run())
loop = asyncio.get_event_loop()
task = loop.create_task(run())

try:
    loop.run_forever()
except Exception as e:
    task.cancel()
    loop.run_until_complete(task)
    raise e
