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
SLAM Launch.

================
Startet slam_toolbox (async, mapping mode) gegen /scan + odom->base_link TF.
Voraussetzung: das Lidar (real: rplidar.launch.py, sim: gubot_one_main
sensor_lidar.xacro) und die EKF-Lokalisierung (gubot_localization/ekf.launch.py)
laufen bereits und publizieren /scan bzw. odom->base_link.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    params_file = LaunchConfiguration("params_file")
    params_file_dec = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(
            get_package_share_directory("gubot_navigation"),
            "config",
            "slam_toolbox_params.yaml",
        ),
        description="Pfad zur slam_toolbox Params-Datei.",
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    use_sim_time_dec = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Sim-Time fuer slam_toolbox aktivieren.",
    )

    slam_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            params_file_dec,
            use_sim_time_dec,
            slam_node,
        ]
    )
