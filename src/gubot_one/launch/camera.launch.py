#!/usr/bin/env python3
"""
Camera Launch File - USB Kamera Konfiguration
==============================================
Startet v4l2_camera Node für USB-Kamera

Hardware:
- USB Kamera an /dev/video0

Ausgabe:
- Topic: /camera/image_raw (sensor_msgs/Image)
- Topic: /camera/camera_info (sensor_msgs/CameraInfo)

Verwendung:
  ros2 launch gubot_one camera.launch.py
"""
import os

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():



    return LaunchDescription([

        Node(
            package='v4l2_camera',  # Video4Linux2 Kamera-Treiber
            executable='v4l2_camera_node',
            output='screen',
            namespace='camera',  # Alle Topics unter /camera/*
            parameters=[{
                'video_device': '/dev/video0',  # USB Kamera Device
                'image_size': [640,480],  # Auflösung: 640x480 Pixel
                'time_per_frame': [1, 6],  # FPS: 6 Bilder/Sekunde (1/6)
                'camera_frame_id': 'camera_link_optical'  # TF Frame für Kamera
                }]
    )
    ])
