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
Record Scan Launch.

===================
Zeichnet die rohen Lidar-Scans (+ TF/Odometry, die zum Nachbauen einer Karte
noetig sind) als rosbag2 auf, damit eine Area auch OHNE das laufende
slam_toolbox spaeter erneut gemappt/analysiert werden kann.

  ros2 launch gubot_navigation record_scan.launch.py bag_name:=area1
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    # realpath() folgt dem --symlink-install Symlink zurueck auf die echte
    # Quelldatei (src/gubot_navigation/launch/record_scan.launch.py), damit
    # der Default in src/gubot_navigation/scans zeigt statt in install/ —
    # sonst geht die Aufnahme bei einem Rebuild/Wechsel verloren und ist
    # nicht versioniert.
    _this_launch_dir = os.path.dirname(os.path.realpath(__file__))
    _package_source_dir = os.path.dirname(_this_launch_dir)

    scans_dir = LaunchConfiguration("scans_dir")
    scans_dir_dec = DeclareLaunchArgument(
        "scans_dir",
        default_value=os.path.join(_package_source_dir, "scans"),
        description="Zielverzeichnis (im Workspace) fuer rosbag2 Aufnahmen.",
    )

    bag_name = LaunchConfiguration("bag_name")
    bag_name_dec = DeclareLaunchArgument(
        "bag_name",
        default_value="scan_recording",
        description="Name der Area/Aufnahme (Unterordner unter scans_dir).",
    )

    record_process = ExecuteProcess(
        cmd=[
            "ros2", "bag", "record",
            "-o", PathJoinSubstitution([scans_dir, bag_name]),
            "/scan", "/tf", "/tf_static", "/odometry/filtered", "/map",
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            scans_dir_dec,
            bag_name_dec,
            record_process,
        ]
    )
