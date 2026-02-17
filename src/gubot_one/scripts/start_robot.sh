#!/bin/bash

# Define workspace path
WORKSPACE_DIR=~/dev_bot

# Check if workspace exists
if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "Error: Workspace directory $WORKSPACE_DIR does not exist."
    exit 1
fi

# Ensure we are in the workspace
cd "$WORKSPACE_DIR"

# Source the workspace
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
else
    echo "Error: install/setup.bash not found in $WORKSPACE_DIR."
    echo "Did you build the workspace?"
    exit 1
fi

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
# Use exec to replace the shell process with ros2 launch
exec ros2 launch gubot_one launch_all_real.launch.py launch_camera:=true
