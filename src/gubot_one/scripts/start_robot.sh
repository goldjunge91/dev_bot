#!/bin/bash

# Ensure we are in the workspace
cd ~/dev_bot

# Source the workspace
source install/setup.bash

# Configure CycloneDDS
# Ensure the config exists, otherwise create a default one
CONFIG_PATH=~/dev_bot/src/gubot_one/cycloneDDS/raspi_cyclonedds.xml
CONFIG_DIR=$(dirname "$CONFIG_PATH")

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Creating default CycloneDDS config at $CONFIG_PATH"
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain Id="any">
    <General>
      <Interfaces>
        <NetworkInterface name="wlan0" priority="default" multicast="default" />
        <NetworkInterface name="eth0" priority="default" multicast="default" />
      </Interfaces>
      <AllowMulticast>true</AllowMulticast>
      <Transport>udp</Transport>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>120</MaxAutoParticipantIndex>
      <Peers>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
EOF
fi

export CYCLONEDDS_URI=file://"$CONFIG_PATH"

# Launch the robot (without camera/lidar by default)
echo "Starting Robot..."
ros2 launch gubot_one launch_all_real.launch.py
