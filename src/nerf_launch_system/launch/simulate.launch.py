# Simulation Launch File für Nerf Standalone System
# Startet Gazebo-Simulation mit ROS2 Control und RViz
#
# Launch-File Struktur:
# 1. Imports - Benötigte Python-Module
# 2. LaunchConfiguration - Variablen für Launch-Argumente
# 3. DeclareLaunchArgument - Definiere konfigurierbare Parameter
# 4. Nodes - ROS2-Knoten die gestartet werden
# 5. LaunchDescription - Rückgabe aller Komponenten

from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    package_name = "nerf_launch_system"

    pkg_nerf = get_package_share_directory("nerf_launch_system")
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")

    # Deklariere 'world' Argument - Welche Gazebo-Welt geladen werden soll
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(
            pkg_nerf, "worlds", "obstacles.world"
        ),  # Standard-Welt mit Hindernissen
        description="World to load",
    )

    # Verarbeite URDF für Simulation (use_hardware=false ist Standard)
    xacro_file = os.path.join(pkg_nerf, "description",
                              "urdf", "nerf_launcher.urdf.xacro")
    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {"robot_description": robot_description_config.toxml()}

    # Robot State Publisher - Publiziert TF-Transformationen basierend auf URDF
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {"use_sim_time": True},
        ],  # Simulationszeit verwenden
    )

    # Gazebo - Physik-Simulator mit ROS2-Integration
    gazebo_params_file = os.path.join(
        get_package_share_directory(
            package_name), "config", "gazebo_params.yaml"
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world": LaunchConfiguration("world"),  # Lade spezifizierte Welt
            "extra_gazebo_args": "--verbose --ros-args --params-file "
            + gazebo_params_file,  # Zusätzliche Gazebo-Parameter
        }.items(),
    )

    # Spawn Entity - Spawnt Roboter in Gazebo aus robot_description
    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic",
            "robot_description",  # Lese URDF von diesem Topic
            "-entity",
            "nerf_launcher",  # Name des Roboters in Gazebo
        ],
        output="screen",
    )

    # RViz Config - Visualisierungs-Konfiguration
    rviz_config = os.path.join(pkg_nerf, "config", "view_v1.rviz")

    # RViz - 3D-Visualisierung für ROS2
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],  # Lade gespeicherte Konfiguration
    )

    # Spawner für Controller - Laden und Aktivieren der Controller
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster"
        ],  # Publiziert Joint-States auf /joint_states
        output="screen",
    )

    trigger_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller"],  # Nerf Tilt/Trigger Controller
        output="screen",
    )

    # flywheel_controller_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["flywheel_controller"],  # Schwungrad-Controller
    #     output="screen",
    # )

    pusher_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller"],  # Dart-Pusher Controller
        output="screen",
    )

    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],  # System Arming/Disarming
        output="screen",
    )

    return LaunchDescription(
        [
            world_arg,
            gazebo,
            node_robot_state_publisher,
            spawn_entity,
            joint_state_broadcaster_spawner,
            trigger_controller_spawner,
            # flywheel_controller_spawner,
            pusher_controller_spawner,
            arming_controller_spawner,
            rviz,
        ]
    )
