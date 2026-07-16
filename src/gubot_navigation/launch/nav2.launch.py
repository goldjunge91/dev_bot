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
Nav2 Komplett-Launch (Lokalisierung + Navigation).

==================================================
Startet wahlweise:
  slam:=false (Standard) -> map_server + AMCL gegen gespeicherte Karte
  slam:=true             -> slam_toolbox (Online-Mapping, map->odom TF)
plus in beiden Fällen die Nav2-Serverkette (navigation.launch.py).

Voraussetzung: Basis-Bringup läuft (Controller, EKF, Lidar) —
real: gubot_bringup/launch_all_real.launch.py launch_lidar:=true
sim:  gubot_gazebo/simulation.launch.py

Verwendung:
  ros2 launch gubot_navigation nav2.launch.py
  ros2 launch gubot_navigation nav2.launch.py slam:=true
  ros2 launch gubot_navigation nav2.launch.py map:=/pfad/karte.yaml
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share = get_package_share_directory("gubot_navigation")
    launch_dir = os.path.join(pkg_share, "launch")

    slam = LaunchConfiguration("slam")
    slam_dec = DeclareLaunchArgument(
        "slam",
        default_value="false",
        description="true: slam_toolbox statt map_server+AMCL.",
    )

    map_yaml = LaunchConfiguration("map")
    map_dec = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(pkg_share, "maps", "test_area.yaml"),
        description="Karten-YAML (nur bei slam:=false).",
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
        description="Sim-Time aktivieren.",
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, "localization.launch.py")
        ),
        launch_arguments={
            "map": map_yaml,
            "params_file": params_file,
            "use_sim_time": use_sim_time,
        }.items(),
        condition=UnlessCondition(slam),
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "slam.launch.py")),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
        condition=IfCondition(slam),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_dir, "navigation.launch.py")
        ),
        launch_arguments={
            "params_file": params_file,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    return LaunchDescription(
        [
            slam_dec,
            map_dec,
            params_file_dec,
            use_sim_time_dec,
            localization,
            slam_launch,
            navigation,
        ]
    )
