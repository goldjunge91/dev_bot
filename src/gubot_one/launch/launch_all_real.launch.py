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
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
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

    camera_type = LaunchConfiguration("camera_type")
    camera_type_arg = DeclareLaunchArgument(
        "camera_type",
        default_value="v4l2",
        description="Type of camera driver to use (v4l2 or usb_cam)",
    )

    auto_arm = LaunchConfiguration("auto_arm")
    auto_arm_arg = DeclareLaunchArgument(
        "auto_arm",
        default_value="false",
        description="Auto-arm the Nerf launcher on startup",
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
            "auto_arm": auto_arm,
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

    # Argument: Gesichtserkennung starten?
    launch_face_tracker_arg = DeclareLaunchArgument(
        "launch_face_tracker",
        default_value="false",
        description="Whether to launch the face tracker",
    )

    target_person = LaunchConfiguration("target_person")
    target_person_arg = DeclareLaunchArgument(
        "target_person",
        default_value="",
        description="Target person for face tracking",
    )

    allow_search = LaunchConfiguration("allow_search")
    allow_search_arg = DeclareLaunchArgument(
        "allow_search",
        default_value="false",
        description="Allow robot to search (rotate) if no face is found",
    )

    launch_face_tracker = LaunchConfiguration("launch_face_tracker")

    # Kamera-Treiber Auswahl
    # 1. v4l2_camera (Standard)
    v4l2_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "camera.launch.py",
                )
            ]
        ),
        condition=IfCondition(
            PythonExpression(
                [
                    "('",
                    launch_camera,
                    "' == 'true') and ('",
                    camera_type,
                    "' == 'v4l2')",
                ]
            )
        ),
    )

    # 2. usb_cam (Alternative, optimiert auf MJPEG)
    usb_cam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "real_camera.launch.py",
                )
            ]
        ),
        condition=IfCondition(
            PythonExpression(
                [
                    "('",
                    launch_camera,
                    "' == 'true') and ('",
                    camera_type,
                    "' == 'usb_cam')",
                ]
            )
        ),
    )

    # Gesichtserkennung modular einbinden
    # Das Bild wird von real_camera.launch.py bereitgestellt.
    face_tracker_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("face_tracker"),
                    "launch",
                    "face_tracker.launch.py",
                )
            ]
        ),
        launch_arguments={
            "image_topic": "/camera/image_raw",  # Nutzt das Bild von real_camera.launch.py
            "target_person": target_person,
            "allow_search": allow_search,
        }.items(),
        condition=IfCondition(launch_face_tracker),
    )

    # Verzögere den Start der Gesichtserkennung, damit die Hardware sicher bereit ist
    delayed_face_tracker_launch = TimerAction(
        period=12.0, actions=[face_tracker_launch]
    )

    return LaunchDescription(
        [
            launch_lidar_arg,
            launch_camera_arg,
            launch_face_tracker_arg,
            target_person_arg,
            allow_search_arg,
            camera_type_arg,
            auto_arm_arg,
            base_launch,
            lidar_launch,
            v4l2_camera_launch,
            usb_cam_launch,
            delayed_face_tracker_launch,
        ]
    )
