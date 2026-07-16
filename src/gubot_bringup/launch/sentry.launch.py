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
Sentry Launch — Nav2 + Face Tracking + Nerf-Feuer.

==================================================
Startet die komplette Sentry-Kette auf einem bereits laufenden
Basis-Bringup (Controller, EKF, Lidar, Kamera, Nerf-Hardware):

1. Nav2 (gubot_navigation/nav2.launch.py)
   - slam:=false: AMCL gegen gespeicherte Karte (Standard: test_area)
   - slam:=true:  slam_toolbox Online-Mapping
   - fährt über /cmd_vel_nav (twist_mux Priorität 10)
2. Face Tracker (face_tracker/face_tracker.launch.py)
   - detect_face + follow_face (/cmd_vel_tracker, Priorität 20)
   - fire_at_face: ruft /nerf/fire (Trigger) wenn Ziel zentriert & nah

Prioritäten (twist_mux): Joystick 100 > Tracker 20 > Nav2 10 —
der Tracker übersteuert Nav2, der Joystick übersteuert alles.

Voraussetzung real:
  ros2 launch gubot_bringup launch_all_real.launch.py \
      launch_lidar:=true launch_camera:=true use_nerf_hardware:=true

Verwendung:
  ros2 launch gubot_bringup sentry.launch.py
  ros2 launch gubot_bringup sentry.launch.py slam:=true
  ros2 launch gubot_bringup sentry.launch.py target_person:=Marco
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    nav_share = get_package_share_directory("gubot_navigation")
    face_share = get_package_share_directory("face_tracker")

    slam = LaunchConfiguration("slam")
    slam_dec = DeclareLaunchArgument(
        "slam",
        default_value="false",
        description="true: slam_toolbox statt AMCL+Karte.",
    )

    map_yaml = LaunchConfiguration("map")
    map_dec = DeclareLaunchArgument(
        "map",
        default_value=os.path.join(nav_share, "maps", "test_area.yaml"),
        description="Karten-YAML für AMCL (nur slam:=false).",
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    use_sim_time_dec = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Sim-Time aktivieren.",
    )

    target_person = LaunchConfiguration("target_person")
    target_person_dec = DeclareLaunchArgument(
        "target_person",
        default_value="",
        description="Zu verfolgende/beschießende Person (leer = beliebig).",
    )

    image_topic = LaunchConfiguration("image_topic")
    image_topic_dec = DeclareLaunchArgument(
        "image_topic",
        default_value="/camera/image_raw",
        description="Eingangs-Bildtopic für detect_face.",
    )

    launch_face_tracker = LaunchConfiguration("launch_face_tracker")
    launch_face_tracker_dec = DeclareLaunchArgument(
        "launch_face_tracker",
        default_value="true",
        description="Face-Tracking + Feuer-Kette starten.",
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, "launch", "nav2.launch.py")
        ),
        launch_arguments={
            "slam": slam,
            "map": map_yaml,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    face_tracker = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(face_share, "launch", "face_tracker.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "target_person": target_person,
            "image_topic": image_topic,
            "cmd_vel_topic": "/cmd_vel_tracker",
        }.items(),
        condition=IfCondition(launch_face_tracker),
    )

    return LaunchDescription(
        [
            slam_dec,
            map_dec,
            use_sim_time_dec,
            target_person_dec,
            image_topic_dec,
            launch_face_tracker_dec,
            nav2,
            face_tracker,
        ]
    )
