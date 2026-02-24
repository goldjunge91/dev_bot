"""
Launch All Real - Hauptstartdatei für echten Roboter
====================================================
Startet alle Komponenten für den echten Gubot One Roboter

Komponenten:
1. Roboter-Basis (launch_robot.launch.py)
   - State Publisher
   - Controller Manager
   - Hardware Interfaces
   - Twist Mux
   - Nerf Launcher (optional)

2. RPLidar (optional)
   - Laser-Scanner für Navigation

3. USB Kamera (optional)
   - Bildverarbeitung

Launch Arguments:
- launch_lidar: false (Standard, da kein Lidar vorhanden)
- launch_camera: false (Standard, da Kamera defekt)
- use_nerf_hardware: true (wird an launch_robot weitergegeben)

Verwendung:
  ros2 launch gubot_one launch_all_real.launch.py
  ros2 launch gubot_one launch_all_real.launch.py launch_lidar:=true
  ros2 launch gubot_one launch_all_real.launch.py launch_camera:=true
  ros2 launch gubot_one launch_all_real.launch.py launch_camera:=true launch_lidar:=true
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


def generate_launch_description():
    package_name = "gubot_one"

    # Launch Configuration Variablen
    launch_lidar = LaunchConfiguration("launch_lidar")
    launch_camera = LaunchConfiguration("launch_camera")

    # Argument: Lidar starten?
    launch_lidar_arg = DeclareLaunchArgument(
        "launch_lidar",
        default_value="false",  # Standard: false (kein Lidar vorhanden)
        description="Whether to launch the RPLidar",
    )

    # Argument: Kamera starten?
    launch_camera_arg = DeclareLaunchArgument(
        "launch_camera",
        default_value="false",  # Standard: false
        description="Whether to launch the USB Camera",
    )

    # Roboter-Basis starten
    # Enthält: State Publisher, Controller Manager, Hardware Interfaces, Twist Mux
    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "launch_robot.launch.py",
                )
            ]
        ),
        launch_arguments={
            "use_nerf_hardware": "true",  # Nerf Launcher aktivieren
        }.items(),
    )

    # RPLidar starten (nur wenn launch_lidar=true)
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "rplidar.launch.py",
                )
            ]
        ),
        condition=IfCondition(launch_lidar),  # Nur starten wenn aktiviert
    )

    # USB Kamera starten (nur wenn launch_camera=true)
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "real_camera.launch.py",
                )
            ]
        ),
        condition=IfCondition(launch_camera),  # Nur starten wenn aktiviert
    )

    return LaunchDescription(
        [launch_lidar_arg, launch_camera_arg, base_launch, lidar_launch, camera_launch]
    )
