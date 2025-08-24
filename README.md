# METARMap Project

A comprehensive aviation weather display system with both LED strip and OLED display components.

## Project Structure

```
METARMap/
├── led/                    # LED strip display component
│   ├── metar.py           # Main LED application
│   ├── airports.py        # LED control and fading logic
│   ├── metar_data.py      # Weather data fetching
│   ├── constants.py       # Hardware configuration
│   ├── airports           # List of airport codes
│   └── test.py           # LED test utility
├── oled/                  # OLED display component
│   ├── main.py           # Main OLED application
│   ├── draw.py           # OLED drawing and display logic
│   ├── airport.py        # OLED weather data handling
│   └── config.py         # OLED configuration
├── shared_logger.py       # Shared logging configuration
├── metarmap.service      # LED systemd service
├── oled-display.service  # OLED systemd service
└── installation scripts
```

## Components

### LED Strip Display
- Displays aviation weather on NeoPixel LED strips
- Colors represent flight categories (VFR=green, MVFR=blue, IFR=red, LIFR=purple)
- Smooth fading animation for windy conditions
- Brightness dimming based on sunrise/sunset times

### OLED Display
- Shows detailed weather information on SSD1306 OLED display
- Cycles through different weather parameters
- Scrolling text for long information
- Configurable display values and timing

## Installation

### LED Service
```bash
sudo ./install_service.sh
```

### OLED Service
```bash
sudo ./install_oled_service.sh
```

## Usage

### LED Commands
```bash
sudo systemctl start metarmap      # Start LED service
sudo systemctl stop metarmap       # Stop LED service
sudo journalctl -u metarmap -f     # View LED logs
```

### OLED Commands
```bash
sudo systemctl start oled-display  # Start OLED service
sudo systemctl stop oled-display   # Stop OLED service
sudo journalctl -u oled-display -f # View OLED logs
```

## Configuration

### LED Configuration
- Edit `led/constants.py` for hardware settings
- Edit `led/airports` file for airport list
- Modify fade timing and colors as needed

### OLED Configuration
- Edit `oled/config.py` for display settings
- Configure airport code in `oled/airport.py`
- Adjust cycle time and displayed values

Both services can run independently and simultaneously.