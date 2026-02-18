#!/bin/bash

# Default Target (from previous session)
DEFAULT_TARGET="ros@192.168.178.45"

TARGET=${1:-$DEFAULT_TARGET}

echo "========================================"
echo "Deploying encodings.pkl to $TARGET"
echo "========================================"

# Check if file exists
if [ ! -f ~/.ros/face_detector/encodings.pkl ]; then
    echo "Error: ~/.ros/face_detector/encodings.pkl not found!"
    exit 1
fi

# Create remote directory (just in case)
ssh $TARGET "mkdir -p ~/.ros/face_detector"

# Rsync file
rsync -avz --progress ~/.ros/face_detector/encodings.pkl $TARGET:~/.ros/face_detector/

if [ $? -eq 0 ]; then
    echo "========================================"
    echo "✅ Success! file deployed."
    echo " You may need to restart the robot launch file to load new faces."
    echo "========================================"
else
    echo "❌ Error during deployment."
fi
