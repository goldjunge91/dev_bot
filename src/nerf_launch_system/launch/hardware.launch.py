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
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_nerf = get_package_share_directory("nerf_launch_system")

    # Verarbeite URDF mit Hardware-Flag (use_hardware=true)
    xacro_file = os.path.join(pkg_nerf, "description", "urdf", "nerf_launcher.urdf.xacro")

    arg_port = DeclareLaunchArgument(
        "port",
        default_value="/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00",
        description="Serial port for Nerf Arduino",
    )

    # xacro-Mappings brauchen zur Launch-Zeit aufgelöste Strings — eine
    # LaunchConfiguration direkt in `mappings` wird von xacro.process_file()
    # nicht aufgelöst (Parse-Zeit != Launch-Zeit). Command(['xacro ...'])
    # lässt xacro als Subprozess mit den fertig substituierten Argumenten
    # laufen; ParameterValue(value_type=str) verhindert, dass robot_state_publisher
    # das Ergebnis als YAML statt als String interpretiert.
    robot_description_content = Command(
        [
            "xacro ",
            xacro_file,
            " use_hardware:=true",
            " port:=",
            LaunchConfiguration("port"),
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    # Robot State Publisher - Publiziert TF-Transformationen basierend auf URDF
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        # Echte Zeit verwenden
        parameters=[robot_description, {"use_sim_time": False}],
    )

    # Controller Manager (ros2_control_node) - Verwaltet alle Hardware-Interfaces und Controller
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            robot_description,
            os.path.join(pkg_nerf, "config", "controllers.yaml"),  # Controller-Konfiguration
            {"use_sim_time": False},  # Echte Zeit verwenden
        ],
        output="screen",
        emulate_tty=True,  # Verbesserte Konsolen-Ausgabe
    )

    # Spawner - ein kombinierter Aufruf statt vier parallele Node-Actions:
    # verhindert eine Race gegen nerf_control (s.u.) — vier unabhängige
    # Spawner liefen bisher parallel zu nerf_control_node, dessen Publisher
    # (u.a. der 1s-Init-Homing auf tilt_max) an einen noch nicht aktiven
    # trigger_controller-Subscriber gingen und bei volatiler QoS
    # stillschweigend verworfen wurden. Combined-Spawner-Muster wie
    # gubot_controller/launch/controller.launch.py.
    controllers_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",  # Publiziert Joint-States auf /joint_states
            "trigger_controller",  # Nerf Tilt/Trigger Controller
            "pusher_controller",  # Dart-Pusher Controller
            "arming_controller",  # System Arming/Disarming
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "60",
        ],
        output="screen",
    )

    # High-Level Control Node - Koordiniert Nerf-Aktionen (Schießen, Zielen).
    # Startet erst NACH dem Spawner (OnProcessExit), damit trigger_controller
    # etc. bereits aktiv sind, bevor nerf_control_node Kommandos weiterleitet.
    nerf_control = Node(
        package="nerf_launch_system",
        executable="nerf_control_node",
        output="screen",
    )

    delayed_nerf_control = RegisterEventHandler(
        OnProcessExit(
            target_action=controllers_spawner,
            on_exit=[nerf_control],
        )
    )

    return LaunchDescription(
        [
            arg_port,
            node_robot_state_publisher,
            controller_manager,
            controllers_spawner,
            delayed_nerf_control,
        ]
    )
