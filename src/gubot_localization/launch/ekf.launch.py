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
EKF Localization Launch.

=======================
Startet den robot_localization EKF-Knoten.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_localization/launch/ekf.launch.py

Änderungen:
- use_sim_time Argument und per-Node-Parameter entfernt
  NEU: use_sim_time wird global durch SetParameter(use_sim_time=True) in simulation.launch.py
       gesetzt und propagiert automatisch an alle Nodes
- /diagnostics Remap hinzugefügt (Referenz-Pattern)
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = "gubot_localization"

    ekf_config = PathJoinSubstitution(
        [
            FindPackageShare(package_name),
            "config",
            "ekf.yaml",
        ]
    )

    # NEU: use_sim_time kommt vom globalen SetParameter in simulation.launch.py
    robot_localization_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_node",
        parameters=[ekf_config],
        # NEU: /diagnostics Remap wie Referenz
        remappings=[("/diagnostics", "diagnostics")],
    )

    return LaunchDescription(
        [
            robot_localization_node,
        ]
    )
