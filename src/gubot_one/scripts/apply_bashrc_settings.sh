#!/bin/bash

BASHRC="$HOME/.bashrc"
BACKUP="$HOME/.bashrc.bak.$(date +%F_%H%M%S)"

echo "Backing up .bashrc to $BACKUP..."
cp "$BASHRC" "$BACKUP"

echo "Appending ROS 2 configuration to $BASHRC..."

cat >> "$BASHRC" << 'EOF'

# --- GUBOT ONE ROS 2 SETUP ---
alias ws='source install/setup.bash'

# Source ROS 2
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
fi

if [ -f /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash ]; then
    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
fi

# CycloneDDS Configuration
export ROS_DOMAIN_ID=0
export CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# -----------------------------
EOF

echo "✅ Updated .bashrc. Please run 'source ~/.bashrc' to apply changes."
