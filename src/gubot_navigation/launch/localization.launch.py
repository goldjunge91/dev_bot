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
Nav2 Localization Launch.

=========================
Startet map_server + AMCL + Lifecycle Manager gegen eine gespeicherte Karte.
Voraussetzung: /scan und odom->base_link TF (EKF) laufen bereits.

Verwendung:
  ros2 launch gubot_navigation localization.launch.py
  ros2 launch gubot_navigation localization.launch.py map:=/pfad/zu/karte.yaml
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("gubot_navigation")

    map_yaml = LaunchConfiguration("map")
    map_dec = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(pkg_share, "maps", "test_area.yaml"),
        description="Pfad zur Karten-YAML (nav2_map_server).",
    )

    params_file = LaunchConfiguration("params_file")
    params_file_dec = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(pkg_share, "config", "nav2_params.yaml"),
        description="Pfad zur Nav2 Params-Datei.",
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    use_sim_time_dec = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Sim-Time für Localization aktivieren.",
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            params_file,
            {"use_sim_time": use_sim_time, "yaml_filename": map_yaml},
        ],
    )

    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_server", "amcl"],
            }
        ],
    )

    return LaunchDescription(
        [
            map_dec,
            params_file_dec,
            use_sim_time_dec,
            map_server,
            amcl,
            lifecycle_manager,
        ]
    )
