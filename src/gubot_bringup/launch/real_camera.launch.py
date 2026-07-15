#!/usr/bin/env python3
"""
Real Camera Launch - USB Kamera für echten Roboter
===================================================
Startet usb_cam Node für USB-Kamera

Hardware:
- USB Kamera an /dev/video0
- Auflösung: 640x480
- Framerate: 15 FPS
- Format: YUYV → BGR8

Topics:
- /image_raw (sensor_msgs/Image)
- /camera_info (sensor_msgs/CameraInfo)

Launch Arguments:
- camera_namespace: 'real_camera' (Standard)
  Trennt echte Kamera von simulierter Kamera

Verwendung:
  ros2 launch gubot_bringup real_camera.launch.py
  ros2 launch gubot_bringup real_camera.launch.py camera_namespace:=my_camera

HINWEIS: Namespace ist temporär deaktiviert (kann Crash verursachen)

Aufbau:
1. DeclareLaunchArgument - Definiert camera_namespace Argument
2. Node - usb_cam_node_exe mit Kamera-Parametern
3. LaunchDescription - Kombiniert Arguments und Node
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument


def generate_launch_description():

    # Launch Configuration Variable

    # Argument: Namespace für Kamera-Topics
    camera_namespace_arg = DeclareLaunchArgument(
        "camera_namespace",
        default_value="real_camera",
        description="Namespace for the real USB camera topics",
    )

    # USB Kamera Node
    usb_cam_node = Node(
        package="usb_cam",
        executable="usb_cam_node_exe",
        name="usb_cam",
        namespace="camera",  # Alle Topics unter /camera/*
        output="log",
        parameters=[
            {
                "video_device": "/dev/video0",  # USB Kamera Device
                "pixel_format": "mjpeg2rgb",  # WICHTIG: v4l2_camera nutzt 'mjpeg', usb_cam braucht 'mjpeg2rgb'
                "output_encoding": "bgr8",
                "image_width": 320,  # Reduzierte Auflösung für Tailscale/WLAN
                "image_height": 240,
                "framerate": 10.0,  # 10 Bilder pro Sekunde
                "camera_name": "real_cam",  # Name für Kalibrierung
                "frame_id": "camera_link_optical",  # TF Frame
            }
        ],
    )

    return LaunchDescription([camera_namespace_arg, usb_cam_node])
