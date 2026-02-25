#!/bin/bash

# Dieses Skript erstellt einen Symlink (Verknüpfung) der Kamera-Kalibrierung
# aus dem Repository in den von ROS 2 erwarteten Ordner ~/.ros/camera_info/

echo "Richte Kamera-Kalibrierung ein..."

# Finde den absoluten Pfad zum Repository (wo dieses Skript liegt)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
REPO_CALIB_FILE="$WORKSPACE_DIR/config/camera_info/real_cam.yaml"

# Zielordner für ROS 2
ROS_CAM_INFO_DIR="$HOME/.ros/camera_info"
TARGET_LINK="$ROS_CAM_INFO_DIR/real_cam.yaml"

# Überprüfe, ob die Kalibrierungsdatei im Repo existiert
if [ ! -f "$REPO_CALIB_FILE" ]; then
    echo "❌ Fehler: Kalibrierungsdatei nicht gefunden in: $REPO_CALIB_FILE"
    exit 1
fi

# Erstelle den ROS 2 camera_info Ordner, falls er nicht existiert
mkdir -p "$ROS_CAM_INFO_DIR"

# Wenn bereits eine echte Datei (kein Symlink) existiert, warne den Nutzer
if [ -f "$TARGET_LINK" ] && [ ! -L "$TARGET_LINK" ]; then
    echo "⚠️ Es existiert bereits eine echte Datei unter $TARGET_LINK."
    echo "Sichere Date backup_real_cam.yaml..."
    mv "$TARGET_LINK" "${TARGET_LINK}.backup"
fi

# Wenn bereits ein Symlink existiert, lösche ihn, um ihn neu zu setzen
if [ -L "$TARGET_LINK" ]; then
    rm "$TARGET_LINK"
fi

# Erstelle den Symlink
ln -s "$REPO_CALIB_FILE" "$TARGET_LINK"

echo "✅ Symlink erfolgreich erstellt:"
echo "   $TARGET_LINK -> $REPO_CALIB_FILE"
echo "Der Kameratreiber wird diese Datei beim nächsten Start automatisch finden."
