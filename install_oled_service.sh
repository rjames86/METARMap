#!/bin/bash

# OLED Display Service Installation Script

set -e

echo "Installing OLED Display systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Copy service file to systemd directory
echo "Copying service file..."
cp "$SCRIPT_DIR/oled-display.service" /etc/systemd/system/

# Reload systemd to recognize new service
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service to start on boot
echo "Enabling service..."
systemctl enable oled-display.service

echo "OLED Display service installed successfully!"
echo ""
echo "Usage:"
echo "  sudo systemctl start oled-display     # Start the service"
echo "  sudo systemctl stop oled-display      # Stop the service"
echo "  sudo systemctl status oled-display    # Check service status"
echo "  sudo systemctl restart oled-display   # Restart the service"
echo "  sudo journalctl -u oled-display -f    # View live logs"
echo ""
echo "To start the service now, run: sudo systemctl start oled-display"