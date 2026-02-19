#!/bin/bash
set -e

# ROS Version (Humble) laden
source /opt/ros/humble/setup.bash

# Falls du ein spezielles Build-Profil (Debug) übergeben willst
if [ "$BUILD_TYPE" == "Debug" ]; then
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Debug
else
    colcon build --symlink-install
fi

source install/setup.bash