#!/usr/bin/env python3

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

"""
Camera Launch File - USB Kamera Konfiguration.

==============================================
Startet v4l2_camera Node für USB-Kamera

Hardware:
- USB Kamera an /dev/video0

Ausgabe:
- Topic: /camera/image_raw (sensor_msgs/Image)
- Topic: /camera/camera_info (sensor_msgs/CameraInfo)

Verwendung:
  ros2 launch gubot_bringup camera.launch.py
"""

import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preflight import check_camera, preflight_action  # noqa: E402


def generate_launch_description():

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "check_hardware",
                default_value="true",
                description="Vor dem Start prüfen, ob die Kamera da ist.",
            ),
            preflight_action(check_camera),
            Node(
                package="v4l2_camera",  # Video4Linux2 Kamera-Treiber
                executable="v4l2_camera_node",
                output="screen",
                namespace="camera",  # Alle Topics unter /camera/*
                parameters=[
                    {
                        "video_device": "/dev/video0",  # USB Kamera Device
                        "pixel_format": "YUYV",  # unkomprimiert, stabiler für v4l2
                        "image_size": [
                            320,
                            240,
                        ],  # Reduzierte Auflösung für Tailscale/WLAN
                        "time_per_frame": [1, 10],  # 10 FPS
                        "camera_frame_id": "camera_link_optical",  # TF Frame für Kamera
                    }
                ],
            )
        ]
    )
