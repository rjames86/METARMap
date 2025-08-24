#!/bin/bash

# OLED Display Service Uninstallation Script

set -e

echo "Uninstalling OLED Display systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Stop the service if running
echo "Stopping service..."
systemctl stop oled-display.service 2>/dev/null || true

# Disable the service
echo "Disabling service..."
systemctl disable oled-display.service 2>/dev/null || true

# Remove service file
echo "Removing service file..."
rm -f /etc/systemd/system/oled-display.service

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

echo "OLED Display service uninstalled successfully!"