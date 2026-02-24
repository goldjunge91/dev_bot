#!/bin/bash

SERVICE_NAME="gubot.service"
SERVICE_FILE="gubot.service"
TEMP_SERVICE_FILE="/tmp/$SERVICE_NAME"
INSTALL_PATH="/etc/systemd/system/$SERVICE_NAME"

# Pfade dynamisch ermitteln
# Dieses Skript liegt in src/gubot_one/autostart/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_DIR="$( cd "$SCRIPT_DIR/../../.." && pwd )"
START_SCRIPT_PATH="$WORKSPACE_DIR/src/gubot_one/scripts/start_robot.sh"

echo "Erkannter Workspace: $WORKSPACE_DIR"
echo "Erkanntes Start-Skript: $START_SCRIPT_PATH"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Bitte als root ausführen (sudo)."
  exit 1
fi

# Check if source file exists
SRC_PATH="$SCRIPT_DIR/$SERVICE_FILE"
if [ ! -f "$SRC_PATH" ]; then
    echo "Fehler: $SRC_PATH nicht gefunden."
    exit 1
fi

# Platzhalter ersetzen
echo "Ersetze Platzhalter in Service-Datei..."
sed -e "s|{{WORKSPACE_DIR}}|$WORKSPACE_DIR|g" \
    -e "s|{{START_SCRIPT_PATH}}|$START_SCRIPT_PATH|g" \
    "$SRC_PATH" > "$TEMP_SERVICE_FILE"

echo "Kopiere Service-Datei nach $INSTALL_PATH..."
cp "$TEMP_SERVICE_FILE" "$INSTALL_PATH"
rm "$TEMP_SERVICE_FILE"

echo "Lade systemd daemon neu..."
systemctl daemon-reload

echo "Aktiviere Service..."
systemctl enable "$SERVICE_NAME"

echo "Starte Service..."
systemctl start "$SERVICE_NAME"

echo "Status:"
systemctl status "$SERVICE_NAME" --no-pager

echo "Installation abgeschlossen."
