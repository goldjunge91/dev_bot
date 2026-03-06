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
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    package_name = "nerf_launch_system"

    pkg_nerf = get_package_share_directory("nerf_launch_system")
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")

    # Deklariere 'world' Argument - Welche Gazebo-Welt geladen werden soll
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(pkg_nerf, "worlds", "empty.world"),
        description="World to load (e.g. empty.world or obstacles.world)",
    )

    use_gazebo_classic_arg = DeclareLaunchArgument(
        "use_gazebo_classic",
        default_value="false",
        description="Whether to use Gazebo Classic (true) or modern Gazebo Ignition/Harmonic (false)",  # noqa: E501
    )

    use_gazebo_classic = LaunchConfiguration("use_gazebo_classic")

    def launch_setup(context):
        use_classic = (
            context.launch_configurations.get("use_gazebo_classic", "false").lower()
            == "true"
        )
        xacro_file = os.path.join(
            pkg_nerf, "description", "urdf", "launcher.urdf.xacro"
        )
        robot_description_config = xacro.process_file(
            xacro_file,
            mappings={"use_gazebo_classic": "true" if use_classic else "false"},
        )

        node_robot_state_publisher = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[
                {"use_sim_time": True},
                {"robot_description": robot_description_config.toxml()},
            ],
        )
        return [node_robot_state_publisher]

    # Gazebo Classic - Physik-Simulator mit ROS2-Integration
    gazebo_params_file = os.path.join(
        get_package_share_directory(package_name), "config", "gazebo_params.yaml"
    )
    gazebo_classic = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world": LaunchConfiguration("world"),  # Lade spezifizierte Welt
            "extra_gazebo_args": "--verbose --ros-args --params-file "
            + gazebo_params_file,  # Zusätzliche Gazebo-Parameter
        }.items(),
        condition=IfCondition(use_gazebo_classic),
    )

    # Spawn Entity in Gazebo Classic
    spawn_entity_classic = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic",
            "robot_description",
            "-entity",
            "nerf_launcher",
        ],
        output="screen",
        condition=IfCondition(use_gazebo_classic),
    )

    # Modern Gazebo (Ignition)
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")
    gazebo_ign = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": [LaunchConfiguration("world"), " -r -v 4 --render-engine ogre"]
        }.items(),
        condition=UnlessCondition(use_gazebo_classic),
    )

    # Spawn Entity in Modern Gazebo (Ignition)
    spawn_entity_ign = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "nerf_launcher",
            "-z",
            "0.5",
        ],
        output="screen",
        condition=UnlessCondition(use_gazebo_classic),
    )

    # ROS-GZ Bridge (nur für Modern Gazebo)
    # Brückt /clock für use_sim_time
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
        condition=UnlessCondition(use_gazebo_classic),
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
            use_gazebo_classic_arg,
            world_arg,
            OpaqueFunction(function=launch_setup),
            gazebo_classic,
            spawn_entity_classic,
            gazebo_ign,
            spawn_entity_ign,
            ros_gz_bridge,
            joint_state_broadcaster_spawner,
            trigger_controller_spawner,
            # flywheel_controller_spawner,
            pusher_controller_spawner,
            arming_controller_spawner,
            rviz,
        ]
    )
