# Copyright 2026 goldjunge91
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

"""
Robot State Publisher (RSP) Launch.

===================================
Publiziert die Roboter-Beschreibung (URDF) und TF-Transformationen.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_description/launch/load_urdf.launch.py

Änderungen gegenüber vorheriger Version:
- controller_config Argument hinzugefügt (Pfad wird in xacro injiziert)
- SetParameter(use_sim_time) und SetRemap(/tf, /tf_static) wie Referenz
- PathJoinSubstitution / FindPackageShare statt os.path.join / get_package_share_directory

Launch Arguments:
- use_sim_time: false (Standard) - Nutzt echte Hardware-Zeit
- use_ros2_control: true (Standard) - Aktiviert ros2_control
- use_nerf_hardware: true (Standard) - Nerf Hardware aktivieren
- controller_config: Pfad zu controllers.yaml (Standard: gubot_controller Paket)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch Configuration Variablen
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_ros2_control = LaunchConfiguration("use_ros2_control")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    use_camera = LaunchConfiguration("use_camera")
    controller_config = LaunchConfiguration("controller_config")

    # Xacro-Datei und Parameter
    # Command() führt xacro zur Laufzeit aus und injiziert alle Argumente
    xacro_file = PathJoinSubstitution([
        FindPackageShare("gubot_description"), "urdf", "gubot_one_main.urdf.xacro"
    ])

    robot_description_config = Command([
        "xacro ",
        xacro_file,
        " use_ros2_control:=", use_ros2_control,
        " sim_mode:=", use_sim_time,
        " use_nerf_hardware:=", use_nerf_hardware,
        " use_camera:=", use_camera,
        " use_gazebo_classic:=false",
        # NEU: controller_config wird in xacro injiziert
        " controller_config:=", controller_config,
    ])

    params = {
        "robot_description": ParameterValue(robot_description_config, value_type=str),
    }

    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[params],
    )

    return LaunchDescription([
        # Launch Arguments (Referenz-Reihenfolge: Args zuerst, dann Actions)
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
            "use_nerf_hardware",
            default_value="true",
            description="Enable Nerf hardware if true",
        ),
        DeclareLaunchArgument(
            "use_camera",
            default_value="true",
            description="Include the Gazebo camera sensor in the URDF "
                        "(false: no render sensor, camera TF frames stay).",
        ),
        # NEU: controller_config Argument — Pfad zu controllers.yaml (Referenz-Pattern)
        DeclareLaunchArgument(
            "controller_config",
            default_value=PathJoinSubstitution([
                FindPackageShare("gubot_controller"), "config", "controllers.yaml"
            ]),
            description="Absolute path to controllers.yaml, injected into URDF xacro.",
        ),
        # HINWEIS: SetParameter(use_sim_time) und SetRemap werden NICHT hier gesetzt.
        # Sie werden global in simulation.launch.py gesetzt und propagieren
        # durch spawn_robot -> controller.
        node_robot_state_publisher,
    ])
