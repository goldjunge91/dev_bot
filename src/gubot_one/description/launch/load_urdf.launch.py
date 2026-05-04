"""
Robot State Publisher (RSP) Launch
===================================
Publiziert die Roboter-Beschreibung (URDF) und TF-Transformationen

Was macht diese Datei:
1. Lädt URDF/Xacro Datei (gubot_one_main.urdf.xacro)
2. Verarbeitet Xacro mit Parametern
3. Startet robot_state_publisher Node
4. Publiziert /robot_description Topic
5. Publiziert TF-Transformationen zwischen allen Links

Launch Arguments:
- use_sim_time: false (Standard) - Nutzt echte Hardware-Zeit
- use_ros2_control: true (Standard) - Aktiviert ros2_control
- integrated_mode: false (Standard) - Nerf + Basis getrennt
- use_nerf_hardware: true (Standard) - Nerf Hardware aktivieren

Verwendung:
  ros2 launch gubot_one rsp.launch.py
  ros2 launch gubot_one rsp.launch.py use_sim_time:=true
  ros2 launch gubot_one rsp.launch.py integrated_mode:=true

Aufbau einer Launch-Datei:
1. Imports - Benötigte Module
2. generate_launch_description() - Hauptfunktion
3. LaunchConfiguration - Variablen für Launch Arguments
4. DeclareLaunchArgument - Definition der Argumente
5. Nodes - ROS2 Nodes die gestartet werden
6. return LaunchDescription([...]) - Liste aller Komponenten
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Launch Configuration Variablen
    # Diese werden durch Command-Line Arguments gesetzt
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_ros2_control = LaunchConfiguration("use_ros2_control")
    integrated_mode = LaunchConfiguration("integrated_mode")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    use_gazebo_classic = LaunchConfiguration("use_gazebo_classic")

    # URDF Datei verarbeiten
    # Xacro wird zu URDF konvertiert mit den angegebenen Parametern
    pkg_path = os.path.join(get_package_share_directory("gubot_one"))
    xacro_file = os.path.join(pkg_path, "description", "urdf", "gubot_one_main.urdf.xacro")

    # Command() führt xacro zur Laufzeit aus
    robot_description_config = Command(
        [
            "xacro ",
            xacro_file,
            " use_ros2_control:=",
            use_ros2_control,
            " sim_mode:=",
            use_sim_time,
            " integrated_mode:=",
            integrated_mode,
            " use_nerf_hardware:=",
            use_nerf_hardware,
            " use_gazebo_classic:=",
            use_gazebo_classic,
        ]
    )

    # Robot State Publisher Node
    # Publiziert /robot_description und TF-Transformationen
    params = {
        "robot_description": ParameterValue(robot_description_config, value_type=str),
        "use_sim_time": use_sim_time,
    }
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[params],
    )

    # Launch Description zurückgeben
    # Enthält alle Arguments und Nodes
    return LaunchDescription(
        [
            # Launch Arguments Definitionen
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "use_ros2_control",
                default_value="true",
                description="Use ros2_control if true",
            ),
            DeclareLaunchArgument(
                "integrated_mode",
                default_value="true",
                description="Use integrated mode if true",
            ),
            DeclareLaunchArgument(
                "use_nerf_hardware",
                default_value="true",
                description="Enable Nerf hardware if true",
            ),
            DeclareLaunchArgument(
                "use_gazebo_classic",
                default_value="false",
                description="Use Gazebo Classic if true",
            ),
            # Nodes
            node_robot_state_publisher,
        ]
    )
