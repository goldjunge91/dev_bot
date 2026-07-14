"""
Launch All Real - Hauptstartdatei für echten Roboter
====================================================
Startet alle Komponenten für den echten Gubot One Roboter

Komponenten:
1. Controller-Kette (controller/launch/controller.launch.py)
   - Robot State Publisher (via description/launch/load_urdf.launch.py)
   - Controller Manager (ros2_control_node, nur echte Hardware)
   - Controller Spawner (mecanum_drive_controller, imu_broadcaster,
     joint_state_broadcaster) + Nerf-Kette (tilt/shooter/arming + control node)
   - Twist Mux
   # ALT: launch_robot.launch.py — gelöscht, Pfade zeigten auf die alte
   #      Paketstruktur (launch/, config/) und existierten nicht mehr

2. EKF Localization (localization/launch/ekf.launch.py)
   - Publiziert odom -> base_link TF (enable_odom_tf ist im Controller aus)

3. RPLidar (optional)
   - Laser-Scanner für Navigation

4. USB Kamera (optional)
   - Bildverarbeitung

5. Joystick-Teleop (bringup/launch/joystick.launch.py)
   - teleop_node + nerf_joy laufen auf dem Roboter
   - joy_node läuft NICHT hier (launch_joy_node:=false) — er läuft auf der
     Remote-Maschine mit dem Gamepad und publiziert /joy über DDS/Tailscale
   # ALT: war ausgehängt, weil config/joystick.yaml gelöscht war —
   #      wiederhergestellt nach controller/config/joystick.yaml

Launch Arguments:
- launch_lidar: false (Standard, da kein Lidar vorhanden)
- launch_camera: false (Standard, da Kamera defekt)
- auto_arm: false (wird an die Nerf-Kette weitergegeben)

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
    pkg_share = get_package_share_directory(package_name)

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

    # Controller-Kette starten (neue modulare Kette)
    # Enthält: RSP (load_urdf), controller_manager, Spawner, Nerf-Kette, Twist Mux
    # ALT: IncludeLaunchDescription(".../launch/launch_robot.launch.py") —
    #      Datei installierte unter bringup/launch/, Include-Pfad war kaputt
    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share,
                    "controller",
                    "launch",
                    "controller.launch.py",
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": "false",  # Echte Hardware, keine Simulation
            "use_ros2_control": "true",
            "use_nerf_hardware": "true",  # Nerf Launcher aktivieren
            "auto_arm": auto_arm,
        }.items(),
    )

    # Joystick-Teleop — nur der Roboter-Anteil:
    # teleop_node (/joy -> /cmd_vel_joy) + nerf_joy. Der joy_node selbst
    # läuft auf der Remote-Maschine mit dem Gamepad (launch_joy_node:=false).
    joystick_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share,
                    "bringup",
                    "launch",
                    "joystick.launch.py",
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": "false",
            "launch_joy_node": "false",
        }.items(),
    )

    # EKF Localization — publiziert odom -> base_link TF
    # (mecanum_drive_controller hat enable_odom_tf: false)
    ekf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share,
                    "localization",
                    "launch",
                    "ekf.launch.py",
                )
            ]
        ),
    )

    # RPLidar starten (nur wenn launch_lidar=true)
    # ALT: "launch", "rplidar.launch.py" — fehlte das bringup-Präfix
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share,
                    "bringup",
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
    # ALT: "launch", "camera.launch.py" — fehlte das bringup-Präfix
    v4l2_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share,
                    "bringup",
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
    # ALT: "launch", "real_camera.launch.py" — fehlte das bringup-Präfix
    usb_cam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share,
                    "bringup",
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
    # ALT: get_package_share_directory("ball_tracker") — Paket existiert nicht,
    #      crashte die gesamte Launch-Datei beim Parsen (PackageNotFoundError)
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
            joystick_launch,
            ekf_launch,
            lidar_launch,
            v4l2_camera_launch,
            usb_cam_launch,
            delayed_face_tracker_launch,
        ]
    )
