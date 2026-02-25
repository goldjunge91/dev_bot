#!/bin/bash

# Dynamisches Finden des Workspace-Verzeichnisses
# Wir gehen davon aus, dass dieses Skript in src/gubot_one/scripts/ liegt
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_DIR="$( cd "$SCRIPT_DIR/../../.." && pwd )"

echo "Gefundener Workspace: $WORKSPACE_DIR"

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
    echo "Wurde der Workspace mit 'colcon build' gebaut?"
    exit 1
fi

# Standard-Argumente
CAMERA_TYPE="usb_cam" # Standard für Tailscale: usb_cam (MJPEG)
TARGET_PERSON=""
ALLOW_SEARCH="false"
AUTO_ARM="false"

# Parse Argumente (optional)
while [[ $# -gt 0 ]]; do
  case $1 in
    --face)
      LAUNCH_FACE="true"
      shift
      ;;
    --armed)
      AUTO_ARM="true"
      shift
      ;;
    --mjpg)
      CAMERA_TYPE="usb_cam"
      shift
      ;;
    --yuyv)
      CAMERA_TYPE="v4l2"
      shift
      ;;
    --usb-cam) # Abwärtskompatibilität
      CAMERA_TYPE="usb_cam"
      shift
      ;;
    --target)
      TARGET_PERSON="$2"
      shift 2
      ;;
    --search)
      ALLOW_SEARCH="true"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# Prepare ROS launch arguments
ROS_ARGS="launch_camera:=true \
          launch_face_tracker:=$LAUNCH_FACE \
          camera_type:=$CAMERA_TYPE \
          auto_arm:=$AUTO_ARM"

# Only add target_person if not empty to prevent ROS launch "malformed argument" error
if [ -n "$TARGET_PERSON" ]; then
    ROS_ARGS="$ROS_ARGS target_person:=$TARGET_PERSON"
fi

# Always pass allow_search as it has a valid default
ROS_ARGS="$ROS_ARGS allow_search:=$ALLOW_SEARCH"

# Ensure DDS Config is set
if [ -z "$CYCLONEDDS_URI" ]; then
    export CYCLONEDDS_URI=file:///var/tmp/cyclonedds.xml
    echo "Nutze Standard DDS-Konfiguration: $CYCLONEDDS_URI"
fi

# Launch the robot
echo "Starte Roboter (FaceTracking=$LAUNCH_FACE, Camera=$CAMERA_TYPE, Target=${TARGET_PERSON:-'any'})..."
ros2 launch gubot_one launch_all_real.launch.py $ROS_ARGS
