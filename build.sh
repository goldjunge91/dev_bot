#!/bin/bash
set -e

# ROS Version (Humble) laden
source /opt/ros/humble/setup.bash

# Falls du ein spezielles Build-Profil (Debug) übergeben willst
if [ "$BUILD_TYPE" == "Debug" ]; then
    # OLD: colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Debug
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
else
    # OLD: colcon build --symlink-install
    colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
fi

source install/setup.bash