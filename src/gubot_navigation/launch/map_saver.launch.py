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
Map Saver Launch.

=================
Startet nav2_map_server's map_saver_server als Dauerdienst. Solange dieser
laeuft (waehrend slam_toolbox mappt), kann jede aktuell befahrene Area per
Service gesichert werden:

  ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap \
    "{map_topic: /map, \
      map_url: '$(pwd)/src/gubot_navigation/maps/<area_name>', \
      image_format: 'pgm', free_thresh: 0.25, occupied_thresh: 0.65}"

Wichtig: map_url muss in den Workspace zeigen (src/gubot_navigation/maps/),
NICHT in ein Home-Verzeichnis o.ae. — sonst ist die Area nicht versioniert
und geht bei einem Rebuild/Wechsel verloren.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_sim_time_dec = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Sim-Time fuer map_saver_server aktivieren.",
    )

    save_map_timeout = LaunchConfiguration("save_map_timeout")
    save_map_timeout_dec = DeclareLaunchArgument(
        "save_map_timeout",
        default_value="5.0",
        description="Timeout (s) fuer eine einzelne save_map Anfrage.",
    )

    map_saver_node = Node(
        package="nav2_map_server",
        executable="map_saver_server",
        name="map_saver",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "save_map_timeout": save_map_timeout,
                "free_thresh_default": 0.25,
                "occupied_thresh_default": 0.65,
            }
        ],
    )

    lifecycle_manager_node = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_map_saver",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_saver"],
            }
        ],
    )

    return LaunchDescription(
        [
            use_sim_time_dec,
            save_map_timeout_dec,
            map_saver_node,
            lifecycle_manager_node,
        ]
    )
