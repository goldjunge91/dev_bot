#!/bin/bash

SERVICE_NAME="gubot.service"
SERVICE_FILE="gubot.service"
INSTALL_PATH="/etc/systemd/system/$SERVICE_NAME"
SRC_PATH="$(dirname "$0")/$SERVICE_FILE"

echo "Installing $SERVICE_NAME..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)."
  exit 1
fi

# Check if source file exists
if [ ! -f "$SRC_PATH" ]; then
    echo "Error: $SRC_PATH not found."
    exit 1
fi

echo "Copying service file to $INSTALL_PATH..."
cp "$SRC_PATH" "$INSTALL_PATH"

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling service..."
systemctl enable "$SERVICE_NAME"

echo "Starting service..."
systemctl start "$SERVICE_NAME"

echo "Status:"
systemctl status "$SERVICE_NAME" --no-pager

echo "Installation complete."
