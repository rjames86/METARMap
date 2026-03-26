#!/bin/bash

# METARMap Setup Script
# Usage: curl -sSL https://raw.githubusercontent.com/rjames86/METARMap/master/setup.sh | sudo bash

set -e

REPO_URL="https://github.com/rjames86/METARMap.git"
INSTALL_DIR="/METARmaps"
LED_DIR="$INSTALL_DIR/led"
SERVICE_NAME="metarmap"
SERVICE_FILE="/etc/systemd/system/metarmap.service"
LOG_FILE="/var/log/metarmap-setup.log"

# ─── Helpers ──────────────────────────────────────────────────────────────────

log()  { echo "[setup] $*" | tee -a "$LOG_FILE"; }
warn() { echo "[setup] WARNING: $*" | tee -a "$LOG_FILE"; }
die()  { echo "[setup] ERROR: $*" | tee -a "$LOG_FILE" >&2; exit 1; }

# Trap any unexpected error and report the line it happened on
trap 'echo; echo "[setup] FAILED at line $LINENO — check $LOG_FILE for details" | tee -a "$LOG_FILE" >&2' ERR

# Start fresh log
echo "=== METARMap setup started $(date) ===" > "$LOG_FILE"

# ─── Root check ───────────────────────────────────────────────────────────────

if [ "$EUID" -ne 0 ]; then
    die "Please run as root: curl -sSL <url> | sudo bash"
fi

# ─── Disable existing cron jobs ───────────────────────────────────────────────

log "Checking for existing METARMap cron jobs..."

comment_out_metar_cron() {
    local file="$1"
    if [ -f "$file" ] && grep -qi "metar" "$file" 2>/dev/null; then
        log "  Found metar entries in $file — commenting out..."
        # Comment out any line containing metar (case-insensitive) that isn't already commented
        sed -i -E '/^[^#].*[Mm][Ee][Tt][Aa][Rr]/s/^/# DISABLED BY METARMAP SETUP: /' "$file"
    fi
}

# /etc/crontab and /etc/cron.d/*
comment_out_metar_cron "/etc/crontab"
for f in /etc/cron.d/*; do
    comment_out_metar_cron "$f"
done

# /etc/rc.local
comment_out_metar_cron "/etc/rc.local"

# All user crontabs in /var/spool/cron/crontabs/
if [ -d /var/spool/cron/crontabs ]; then
    for f in /var/spool/cron/crontabs/*; do
        comment_out_metar_cron "$f"
    done
fi

# ─── Stop any running metar processes ─────────────────────────────────────────

log "Stopping any running metar processes..."

# Stop systemd service if it exists
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    log "  Stopping $SERVICE_NAME service..."
    systemctl stop "$SERVICE_NAME"
fi

# Kill any stray metar.py processes
if pgrep -f "metar.py" > /dev/null 2>&1; then
    log "  Killing running metar.py processes..."
    pkill -f "metar.py" || true
fi

# ─── Handle existing /METARmaps directory ─────────────────────────────────────

if [ -d "$INSTALL_DIR" ]; then
    if [ -d "$LED_DIR" ]; then
        # Already our directory structure — safe to overwrite
        log "Found existing installation at $LED_DIR — will overwrite."
    else
        # Looks like old-style code sitting directly in /METARmaps
        BACKUP_DIR="${INSTALL_DIR}.bak.$(date +%Y%m%d_%H%M%S)"
        log "Found existing directory at $INSTALL_DIR (likely previous version)."
        log "  Backing up to $BACKUP_DIR..."
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        log "  Backup saved to $BACKUP_DIR"
    fi
fi

# ─── Clone repository ─────────────────────────────────────────────────────────

log "Downloading METARMap..."

# Ensure git is available
if ! command -v git &>/dev/null; then
    log "  git not found — installing..."
    apt-get install -y git
fi

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

git clone --depth=1 "$REPO_URL" "$TEMP_DIR/METARMap"

# ─── Install files ────────────────────────────────────────────────────────────

log "Installing files to $LED_DIR..."
mkdir -p "$LED_DIR"

# Copy LED application files
cp -r "$TEMP_DIR/METARMap/led/." "$LED_DIR/"

# Copy shared logger (referenced by led/metar.py via sys.path)
cp "$TEMP_DIR/METARMap/shared_logger.py" "$INSTALL_DIR/"

# ─── Install Python dependencies ──────────────────────────────────────────────

log "Installing Python packages..."

# Ensure pip is available
if ! command -v pip3 &>/dev/null; then
    log "  pip3 not found — installing..."
    apt-get install -y python3-pip
fi

pip3 install \
    requests \
    astral \
    adafruit-circuitpython-neopixel \
    adafruit-blinka

# ─── Install systemd service ──────────────────────────────────────────────────

log "Installing systemd service..."

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=METAR Map LED Display
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$LED_DIR
ExecStart=/usr/bin/python3 $LED_DIR/metar.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# ─── Post-start health check ──────────────────────────────────────────────────

log "Waiting for service to stabilise..."
sleep 5

if systemctl is-active --quiet "$SERVICE_NAME"; then
    log ""
    log "Installation complete! Service is running."
else
    echo "" | tee -a "$LOG_FILE"
    echo "[setup] !! Service started but then crashed. Recent logs:" | tee -a "$LOG_FILE"
    echo "──────────────────────────────────────────────────────────" | tee -a "$LOG_FILE"
    journalctl -u "$SERVICE_NAME" -n 40 --no-pager | tee -a "$LOG_FILE"
    echo "──────────────────────────────────────────────────────────" | tee -a "$LOG_FILE"
    echo "[setup] Full setup log: $LOG_FILE" | tee -a "$LOG_FILE"
    echo "[setup] To investigate further:" | tee -a "$LOG_FILE"
    echo "[setup]   sudo journalctl -u metarmap -f        # live service logs" | tee -a "$LOG_FILE"
    echo "[setup]   sudo python3 $LED_DIR/metar.py        # run directly to see errors" | tee -a "$LOG_FILE"
    exit 1
fi

log ""
log "The METARMap LED service is running and will start automatically on boot."
log ""
log "Useful commands:"
log "  sudo systemctl status metarmap          # Check status"
log "  sudo systemctl restart metarmap         # Restart"
log "  sudo journalctl -u metarmap -f          # View live logs"
log "  sudo python3 $LED_DIR/metar.py          # Run directly (shows errors inline)"
log ""
log "To customise airports or LED settings, edit:"
log "  $LED_DIR/airports       # Airport list (one ICAO code per line)"
log "  $LED_DIR/constants.py   # LED count, brightness, wind threshold"
log ""
log "Full setup log saved to: $LOG_FILE"
