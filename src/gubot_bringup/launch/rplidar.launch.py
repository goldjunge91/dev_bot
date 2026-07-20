# Copyright 2026 goldjunge91
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preflight import LIDAR_PORT, check_lidar, preflight_action  # noqa: E402


def generate_launch_description():

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "check_hardware",
                default_value="true",
                description="Vor dem Start prüfen, ob das Lidar am Port hängt.",
            ),
            preflight_action(check_lidar),
            Node(
                package="rplidar_ros",
                executable="rplidar_composition",
                output="screen",
                parameters=[
                    {
                        "serial_port": LIDAR_PORT,  # zentral in preflight.py
                        "frame_id": "laser_frame",
                        "angle_compensate": True,
                        "scan_mode": "Standard",
                    }
                ],
            ),
        ]
    )
