import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory("ball_tracker"),
        "config",
        "face_tracker_params.yaml",
    )

    detect_only = LaunchConfiguration("detect_only")
    follow_only = LaunchConfiguration("follow_only")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "detect_only",
                default_value="false",
                description="Nur Detektion (keine Bewegung des Roboters)",
            ),
            DeclareLaunchArgument(
                "follow_only",
                default_value="false",
                description="Nur Verfolgung (keine Bildverarbeitung - erwartet /face_detections)",
            ),
            # 1. Kamera-Treiber (v4l2_camera)
            # Auf dem Pi nutzen wir direkt die Hardware.
            # MJPG 320x240 ist effizient und spart CPU/USB-Last.
            Node(
                package="v4l2_camera",
                executable="v4l2_camera_node",
                output="screen",
                parameters=[
                    {
                        "video_device": "/dev/video0",
                        "image_size": [320, 240],
                        "pixel_format": "MJPG",
                        "output_encoding": "rgb8",
                    }
                ],
                condition=UnlessCondition(follow_only),
            ),
            # 2. Face Detector
            # Abonniert /image_raw (vom Treiber) und publiziert /face_detections
            Node(
                package="ball_tracker",
                executable="detect_face",
                parameters=[params_file],
                remappings=[("/image_in", "/image_raw"), ("/image_out", "/image_out")],
                condition=UnlessCondition(follow_only),
            ),
            # 3. Face Follower
            # Abonniert /face_detections und steuert /cmd_vel
            Node(
                package="ball_tracker",
                executable="follow_face",
                parameters=[params_file],
                remappings=[("/cmd_vel", "/cmd_vel")],
                condition=UnlessCondition(detect_only),
            ),
        ]
    )
