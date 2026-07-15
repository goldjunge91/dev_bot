# Simulation Launch File für Nerf Standalone System
# Startet Gazebo (Ignition Fortress / gz-sim) mit ROS2 Control und RViz
#
# Launch-File Struktur:
# 1. Imports - Benötigte Python-Module
# 2. LaunchConfiguration - Variablen für Launch-Argumente
# 3. DeclareLaunchArgument - Definiere konfigurierbare Parameter
# 4. Nodes - ROS2-Knoten die gestartet werden
# 5. LaunchDescription - Rückgabe aller Komponenten
#
# ALT: Startete Gazebo Classic (gazebo_ros/gazebo.launch.py + spawn_entity.py),
# während die URDF-Sim-Branch das Ignition-Fortress-Plugin (ign_ros2_control)
# lud — beide Hälften der Sim liefen gegeneinander. Jetzt durchgängig
# Ignition Fortress, nach dem etablierten Muster aus gubot_gazebo.

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_nerf = get_package_share_directory("nerf_launch_system")

    # Deklariere 'world' Argument - Welche Gazebo-Welt geladen werden soll
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(pkg_nerf, "worlds", "empty.world"),
        description="Absolute path to the SDF world file to load.",
    )
    world = LaunchConfiguration("world")

    # Verarbeite URDF für Simulation (use_hardware=false ist Standard).
    # Command() lässt xacro als Subprozess mit den fertig substituierten
    # Argumenten laufen (siehe hardware.launch.py für dieselbe Begründung).
    xacro_file = os.path.join(pkg_nerf, "description", "urdf", "nerf_launcher.urdf.xacro")
    robot_description_content = Command(["xacro ", xacro_file])
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    # Robot State Publisher - Publiziert TF-Transformationen basierend auf URDF
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # Gazebo (Ignition Fortress / gz-sim), inkl. Physics/Sensors/SceneBroadcaster
    # Plugins (siehe worlds/empty.world) und GUI.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("husarion_gz_worlds"), "launch", "gz_sim.launch.py"
            )
        ),
        launch_arguments={
            "gz_world": world,
            "gz_log_level": "1",
        }.items(),
    )

    # Globaler Clock-Bridge (nur /clock — die standalone Sim hat keine
    # weiteren Sensor-Topics zu bridgen)
    gz_bridge_config = os.path.join(pkg_nerf, "config", "gz_bridge.yaml")
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        parameters=[{"config_file": gz_bridge_config}],
    )

    # Spawn Entity - Spawnt Roboter in Gazebo aus robot_description
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "nerf_launcher",
            "-allow_renaming", "true",
        ],
        output="screen",
    )

    # RViz Config - Visualisierungs-Konfiguration
    rviz_config = os.path.join(pkg_nerf, "config", "view.rviz")

    # RViz - 3D-Visualisierung für ROS2
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
    )

    # Spawner für Controller - ein kombinierter Aufruf statt vier parallele
    # Node-Actions: verhindert eine Race gegen nerf_control (s.u.) — vier
    # unabhängige Spawner liefen bisher parallel zu nerf_control_node, dessen
    # Publisher (u.a. der 1s-Init-Homing auf tilt_max) an einen noch nicht
    # aktiven trigger_controller-Subscriber gingen und bei volatiler QoS
    # stillschweigend verworfen wurden — der Joint blieb dann einfach auf
    # seinem URDF-initial_value (= tilt_max) stehen, unabhängig vom
    # gesendeten Tilt-Wert. Combined-Spawner-Muster wie
    # gubot_controller/launch/controller.launch.py.
    controllers_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "trigger_controller",  # Nerf Tilt/Trigger Controller
            "pusher_controller",  # Dart-Pusher Controller
            "arming_controller",  # System Arming/Disarming
            "--controller-manager-timeout", "60",
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
            world_arg,
            gz_sim,
            gz_bridge,
            node_robot_state_publisher,
            spawn_entity,
            controllers_spawner,
            delayed_nerf_control,
            rviz,
        ]
    )
