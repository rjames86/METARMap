import asyncio
from airports import AirportLED
from constants import strip
from metar_data import get_metar_data

async def run():
    metar_infos = get_metar_data
    tasks = [AirportLED(strip, index, airport_code, metar_infos[airport_code]).run() for index, airport_code in enumerate(metar_infos.keys())]
    results = asyncio.gather(*tasks)
    try:
        await results
    except Exception:
        print("Cancelling")
        results.cancel()


try:
    asyncio.run(run())
except Exception as e:
    print(e)
    pass
