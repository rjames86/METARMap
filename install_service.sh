#!/bin/bash

# METARMap Service Installation Script

set -e

echo "Installing METARMap systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Copy service file to systemd directory
echo "Copying service file..."
cp "$SCRIPT_DIR/metarmap.service" /etc/systemd/system/

# Reload systemd to recognize new service
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service to start on boot
echo "Enabling service..."
systemctl enable metarmap.service

echo "Service installed successfully!"
echo ""
echo "Usage:"
echo "  sudo systemctl start metarmap     # Start the service"
echo "  sudo systemctl stop metarmap      # Stop the service"
echo "  sudo systemctl status metarmap    # Check service status"
echo "  sudo systemctl restart metarmap   # Restart the service"
echo "  sudo journalctl -u metarmap -f    # View live logs"
echo ""
echo "To start the service now, run: sudo systemctl start metarmap"