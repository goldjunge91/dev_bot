from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_ball_tracker = get_package_share_directory("ball_tracker")

    # Argumente
    detect_only = LaunchConfiguration("detect_only")
    detect_only_arg = DeclareLaunchArgument(
        "detect_only", default_value="true", description="Nur Erkennung, kein Verfolgen"
    )

    # v4l2_camera Node (konfiguriert für YUYV)
    camera_node = Node(
        package="v4l2_camera",
        executable="v4l2_camera_node",
        output="screen",
        parameters=[
            {
                "video_device": "/dev/video0",
                "image_size": [320, 240],
                "pixel_format": "MJPG",  # MJPG ist robuster bei USBIP
                "output_encoding": "rgb8",  # Erzwingt Dekomprimierung
            }
        ],
    )

    # Face Tracker Launch inkludieren
    face_tracker_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ball_tracker, "launch", "face_tracker.launch.py")
        ),
        launch_arguments={
            "detect_only": detect_only,
            "image_topic": "/image_raw",  # v4l2_camera publiziert hier
        }.items(),
    )

    return LaunchDescription([detect_only_arg, camera_node, face_tracker_launch])
