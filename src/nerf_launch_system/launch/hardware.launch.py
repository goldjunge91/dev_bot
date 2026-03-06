# Copyright 2026 Developer
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

# Hardware Launch File für Nerf Standalone System
# Startet ROS2 Control mit echter Hardware (Arduino via Serial)
#
# Launch-File Struktur:
# 1. Imports - Benötigte Python-Module
# 2. LaunchConfiguration - Variablen für Launch-Argumente
# 3. DeclareLaunchArgument - Definiere konfigurierbare Parameter
# 4. Nodes - ROS2-Knoten die gestartet werden
# 5. LaunchDescription - Rückgabe aller Komponenten

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_nerf = get_package_share_directory("nerf_launch_system")

    # Verarbeite URDF mit Hardware-Flag (use_hardware=true)
    xacro_file = os.path.join(pkg_nerf, "description", "urdf", "launcher.urdf.xacro")

    # Deklariere Launch-Argumente
    from launch.actions import DeclareLaunchArgument
    from launch.substitutions import LaunchConfiguration

    arg_port = DeclareLaunchArgument(
        "port",
        # default_value="/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00",  # Standard serieller Port für Arduino  # noqa: E501
        description="Serial port for Nerf Arduino",
    )

    # Verarbeite xacro mit use_hardware=true und port-Parameter
    robot_description_config = xacro.process_file(
        xacro_file,
        mappings={"use_hardware": "true", "port": LaunchConfiguration("port")},
    )
    robot_description = {"robot_description": robot_description_config.toxml()}

    # Robot State Publisher - Publiziert TF-Transformationen basierend auf URDF
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": False}],  # Echte Zeit verwenden
    )

    # Controller Manager (ros2_control_node) - Verwaltet alle Hardware-Interfaces und Controller
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            robot_description,
            os.path.join(
                pkg_nerf, "config", "controllers.yaml"
            ),  # Controller-Konfiguration
            {"use_sim_time": False},  # Echte Zeit verwenden
        ],
        output="screen",
        emulate_tty=True,  # Verbesserte Konsolen-Ausgabe
    )

    # Spawner - Laden und Aktivieren der Controller
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",  # Publiziert Joint-States auf /joint_states
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    trigger_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "trigger_controller",
            "--controller-manager",
            "/controller_manager",
        ],  # Nerf Tilt/Trigger Controller
        output="screen",
    )

    # flywheel_controller = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=[
    #         "flywheel_controller",  # Schwungrad-Controller (ESC)
    #         "--controller-manager",
    #         "/controller_manager",
    #     ],
    #     output="screen",
    # )

    pusher_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "pusher_controller",
            "--controller-manager",
            "/controller_manager",
        ],  # Dart-Pusher Controller
        output="screen",
    )

    arming_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arming_controller",
            "--controller-manager",
            "/controller_manager",
        ],  # System Arming/Disarming
        output="screen",
    )

    # High-Level Control Node - Koordiniert Nerf-Aktionen (Schießen, Zielen)
    nerf_control = Node(
        package="nerf_launch_system",
        executable="nerf_control_node",
        output="screen",
    )

    return LaunchDescription(
        [
            arg_port,
            node_robot_state_publisher,
            controller_manager,
            joint_state_broadcaster,
            trigger_controller,
            # flywheel_controller,
            pusher_controller,
            arming_controller,
            nerf_control,
        ]
    )
