#!/usr/bin/env python3
"""
Diagnostic script — prints the current brightness factor for every airport.
Run with: sudo /root/env/bin/python3 /METARmaps/led/check_brightness.py

Brightness is 0.01 (minimum, nighttime) to 1.0 (full, midday).
"""

import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metar_data import get_metar_data
from airports import AIRPORT_CODES
from sun_calculator import SunCalculator

print("Fetching METAR data...")
metar_infos = get_metar_data()

now = datetime.datetime.now(datetime.timezone.utc)
print(f"Current UTC time: {now.strftime('%H:%M:%S')}\n")
print(f"{'Airport':<8} {'Brightness':>10}  {'Dawn (UTC)':>12}  {'Dusk (UTC)':>12}  {'Status'}")
print("-" * 65)

for code in AIRPORT_CODES:
    info = metar_infos.get(code)
    if info is None or info.latitude is None:
        print(f"{code:<8} {'no data':>10}")
        continue

    calc = SunCalculator(info.latitude, info.longitude)
    factor = calc.calculate_brightness_factor()

    try:
        sun_times = calc.get_current_sun_times()
        dawn = sun_times["dawn"].strftime("%H:%M:%S")
        dusk = sun_times["dusk"].strftime("%H:%M:%S")
    except Exception:
        dawn = dusk = "unknown"

    if factor <= 0.01:
        status = "NIGHT (min brightness)"
    elif factor < 0.5:
        status = "dim (dawn/dusk)"
    else:
        status = "full brightness"

    print(f"{code:<8} {factor:>10.2f}  {dawn:>12}  {dusk:>12}  {status}")
