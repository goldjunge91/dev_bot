#!/bin/bash

# Dieses Skript konfiguriert die .bashrc für ROS 2 und CycloneDDS über Tailscale.
# Es erkennt automatisch, ob es auf dem Pi oder dem PC ausgeführt wird.

BASHRC="$HOME/.bashrc"
BACKUP="$HOME/.bashrc.bak.$(date +%F_%H%M%S)"

echo "Sichere .bashrc nach $BACKUP..."
cp "$BASHRC" "$BACKUP"

echo "Füge ROS 2 Konfiguration zu $BASHRC hinzu..."

# Pfad zum Workspace ermitteln (relativ zum Skript-Speicherort)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WS_PATH="$( cd "$SCRIPT_DIR/../../.." &> /dev/null && pwd )"

cat >> "$BASHRC" << EOF

# --- GUBOT ONE ROS 2 SETUP ---
# Workspace Alias
alias ws='source $WS_PATH/install/setup.bash'

# Source ROS 2
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
fi

# Colcon Autocomplete
if [ -f /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash ]; then
    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
fi

# CycloneDDS Configuration over Tailscale
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=0

HOSTNAME=\$(hostname)
if [ "\$HOSTNAME" = "ros2pi" ]; then
    echo "Identifiziert als ROBOTER (ros2pi)"
    export CYCLONEDDS_URI="file://$WS_PATH/src/gubot_one_bringup/cycloneDDS/raspi_cyclonedds.xml"
else
    echo "Identifiziert als PC (h3mistral/andere)"
    export CYCLONEDDS_URI="file://$WS_PATH/src/gubot_one_bringup/cycloneDDS/pc_cyclonedds.xml"
fi

# Colorized Output
export RCUTILS_COLORIZED_OUTPUT=1
# -----------------------------
EOF

echo "✅ .bashrc aktualisiert. Bitte 'source ~/.bashrc' ausführen."
