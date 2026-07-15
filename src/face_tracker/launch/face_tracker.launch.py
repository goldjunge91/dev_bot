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

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch.conditions import UnlessCondition

import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    params_file = LaunchConfiguration("params_file")
    params_file_dec = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(
            get_package_share_directory("face_tracker"),
            "config",
            "face_tracker_params.yaml",
        ),
        description="Pfad zur Params-Datei für alle face_tracker Nodes.",
    )

    detect_only = LaunchConfiguration("detect_only")
    detect_only_dec = DeclareLaunchArgument(
        "detect_only",
        default_value="false",
        description="Nur detect_face starten, kein follow_face.",
    )

    follow_only = LaunchConfiguration("follow_only")
    follow_only_dec = DeclareLaunchArgument(
        "follow_only", default_value="false", description="Nur follow_face starten."
    )

    use_sim_time = LaunchConfiguration("use_sim_time")
    use_sim_time_dec = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Sim-Time für follow_face aktivieren.",
    )

    image_topic = LaunchConfiguration("image_topic")
    image_topic_dec = DeclareLaunchArgument(
        "image_topic",
        default_value="/camera/image_raw",
        description="Eingangs-Bildtopic (z.B. /image_raw von v4l2_camera).",
    )

    cmd_vel_topic = LaunchConfiguration("cmd_vel_topic")
    cmd_vel_topic_dec = DeclareLaunchArgument(
        "cmd_vel_topic",
        default_value="/cmd_vel_tracker",
        description="Ausgabe-Topic für Fahrbefehle.",
    )

    target_person = LaunchConfiguration("target_person")
    target_person_dec = DeclareLaunchArgument(
        "target_person",
        default_value="",
        description="Name der zu verfolgenden Person (leer = beliebig).",
    )

    allow_search = LaunchConfiguration("allow_search")
    allow_search_dec = DeclareLaunchArgument(
        "allow_search",
        default_value="false",
        description="Ob der Roboter rotieren soll, wenn kein Gesicht gefunden wird.",
    )

    # --- Nodes ---
    detect_node = Node(
        package="face_tracker",
        executable="detect_face",
        parameters=[params_file, {"target_person": target_person}],
        remappings=[("/image_in", image_topic)],
        condition=UnlessCondition(follow_only),
    )

    follow_node = Node(
        package="face_tracker",
        executable="follow_face",
        parameters=[
            params_file,
            {
                "use_sim_time": use_sim_time,
                "target_person": target_person,
                "allow_search": allow_search,
            },
        ],
        remappings=[("/cmd_vel", cmd_vel_topic)],
        condition=UnlessCondition(detect_only),
    )

    fire_node = Node(
        package="face_tracker",
        executable="fire_at_face",
        parameters=[params_file, {"target_person": target_person}],
        condition=UnlessCondition(detect_only),
    )

    return LaunchDescription(
        [
            params_file_dec,
            detect_only_dec,
            follow_only_dec,
            use_sim_time_dec,
            image_topic_dec,
            cmd_vel_topic_dec,
            target_person_dec,
            allow_search_dec,
            detect_node,
            follow_node,
            fire_node,
        ]
    )
