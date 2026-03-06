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

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory("face_tracker"),
        "config",
        "face_tracker_params.yaml",
    )

    detect_only = LaunchConfiguration("detect_only")
    follow_only = LaunchConfiguration("follow_only")

    # UDP Receiver Node (ersetzt v4l2_camera)
    udp_receiver_node = Node(
        package="face_tracker",
        executable="udp_cam_receiver",
        name="udp_cam_receiver",
        parameters=[{"port": 9999}],
        remappings=[("/image_raw", "/image_raw")],
    )

    # Face Tracker (Module!)
    face_tracker_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("face_tracker"),
                "launch",
                "face_tracker.launch.py",
            )
        ),
        launch_arguments={
            "image_topic": "/image_raw",
            "detect_only": detect_only,
            "follow_only": follow_only,
            "params_file": params_file,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "detect_only",
                default_value="false",
                description="Nur Detektion laufen lassen (keine Bewegung)",
            ),
            DeclareLaunchArgument(
                "follow_only",
                default_value="false",
                description="Nur Verfolgung laufen lassen",
            ),
            udp_receiver_node,
            face_tracker_launch,
        ]
    )
