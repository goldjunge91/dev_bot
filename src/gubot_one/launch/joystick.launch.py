#!/usr/bin/env python3
"""
Joystick Launch File - Controller-Steuerung
============================================
Startet Joystick-Nodes für Roboter + Nerf Launcher

Nodes:
1. joy_node - Liest Controller-Eingaben
2. teleop_node - Konvertiert Joy → Twist (Roboter-Bewegung)
3. nerf_joy - Steuert Nerf Launcher

Topics:
- /joy (sensor_msgs/Joy) - Rohe Controller-Daten
- /cmd_vel_joy (geometry_msgs/Twist) - Bewegungsbefehle

Launch Arguments:
- use_sim_time: false (Standard)
- launch_joy_node: true (startet joy_node lokal)

Verwendung:
  ros2 launch gubot_one joystick.launch.py
  ros2 launch gubot_one joystick.launch.py launch_joy_node:=false  # Wenn joy_node woanders läuft
"""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
import launch.conditions as if_condition

import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Launch Configuration Variablen
    use_sim_time = LaunchConfiguration("use_sim_time")
    launch_joy_node = LaunchConfiguration("launch_joy_node")

    # Lade Joystick-Parameter aus YAML
    joy_params = os.path.join(
        get_package_share_directory("gubot_one"), "config", "joystick.yaml"
    )

    # Node 1: joy_node - Liest Controller über /dev/input/js0
    joy_node = Node(
        package="joy",
        executable="joy_node",
        parameters=[joy_params, {"use_sim_time": use_sim_time}],
        condition=if_condition.IfCondition(launch_joy_node),  # Nur starten wenn launch_joy_node=true
    )

    # Node 2: teleop_node - Konvertiert Joy-Nachrichten zu Twist (Roboter-Bewegung)
    teleop_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        name="teleop_node",
        parameters=[joy_params, {"use_sim_time": use_sim_time}],
        remappings=[("/cmd_vel", "/cmd_vel_joy")],  # Output zu /cmd_vel_joy (für twist_mux)
    )

    # DEAKTIVIERT: twist_stamper - Fügt Timestamp zu Twist hinzu
    # twist_stamper = Node(
    #         package='twist_stamper',
    #         executable='twist_stamper',
    #         parameters=[{'use_sim_time': use_sim_time}],
    #         remappings=[('/cmd_vel_in','/diff_cont/cmd_vel_unstamped'),
    #                     ('/cmd_vel_out','/diff_cont/cmd_vel')]
    #      )

    # Node 3: nerf_joy - Steuert Nerf Launcher über Controller
    nerf_joy_node = Node(
        package="gubot_one",
        executable="nerf_joy.py",
        name="nerf_joy",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            # Launch Arguments
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "launch_joy_node",
                default_value="true",
                description="Whether to run joy_node locally",
            ),
            # Nodes
            joy_node,
            teleop_node,
            nerf_joy_node,
            # twist_stamper
        ]
    )
