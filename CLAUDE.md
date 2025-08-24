# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

METARMap is a Python project that displays aviation weather (METAR) data on a NeoPixel LED strip. Each LED represents an airport and displays colors based on flight categories (VFR=green, MVFR=blue, IFR=red, LIFR=purple). LEDs also fade/blink when wind gusts exceed the threshold and dim based on sunrise/sunset times at each airport location.

## Running the Application

- **Main application**: `python3 metar.py` or `sudo python3 metar.py` (requires sudo for hardware access)
- **Test LED strip**: `python3 test.py` (rainbow animation test)
- **Startup script**: `./startup.sh` (runs main application with sudo)

## Architecture

### Core Components

- **metar.py**: Main application entry point, runs continuous loop fetching METAR data every 5 minutes and updating LED colors
- **metar_data.py**: Handles METAR data fetching from FAA Aviation Weather API and XML parsing into MetarInfo objects
- **airports.py**: Contains AirportLED class that manages individual LED behavior including color determination, brightness dimming based on time of day, and wind gust blinking effects
- **constants.py**: Hardware configuration (LED count, pin, brightness) and color mappings for flight categories

### Data Flow

1. `get_metar_data()` fetches XML from aviationweather.gov for all airports
2. XML is parsed into MetarInfo objects containing flight category, wind data, coordinates, etc.  
3. AirportLED objects are created for each airport, mapping to specific LED positions
4. Each LED calculates its color based on flight category and applies brightness/blinking effects
5. All LEDs are updated and displayed on the strip every iteration

### Key Files

- **airports**: Plain text file listing airport codes (ICAO format like KIAH, KDFW) - one per line, determines which airports are displayed and LED mapping order
- **logger.py**: Logging configuration (currently disabled)
- **test.py**: LED strip test utility with rainbow animations

## Hardware Dependencies

This project is designed for Raspberry Pi with NeoPixel LED strips using the `neopixel` and `board` libraries. The constants.py file contains hardware-specific configurations that may need adjustment for different setups.