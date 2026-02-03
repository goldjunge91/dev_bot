#!/bin/bash

# Ensure we are in the workspace
cd ~/dev_bot

# Source the workspace
source install/setup.bash

# Ensure DDS Config is set
# If CYCLONEDDS_URI is NOT set, default to the file setup by setup_dds_config.sh
if [ -z "$CYCLONEDDS_URI" ]; then
    export CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
    echo "Using default DDS config: $CYCLONEDDS_URI"
else
    echo "Using existing DDS config: $CYCLONEDDS_URI"
fi

# Launch the robot
echo "Starting Robot..."
ros2 launch gubot_one launch_all_real.launch.py
