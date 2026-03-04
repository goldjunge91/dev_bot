import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory("face_tracker"),
        "config",
        "face_tracker_params.yaml",
    )

    detect_only = LaunchConfiguration("detect_only")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "detect_only",
                default_value="false",
                description="Nur Detektion (keine Bewegung des Roboters)",
            ),
            # --- SIMULATION ONLY ---
            # Hinweis: Der v4l2_camera_node wird absichtlich NICHT gestartet!
            # Die Kamerabilder kommen stattdessen aus Gazebo (über ros_gz_bridge)
            # auf dem Topic /camera/image_raw
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("face_tracker"),
                        "launch",
                        "face_tracker.launch.py",
                    )
                ),
                launch_arguments={
                    "image_topic": "/camera/image_raw",
                    "params_file": params_file,
                }.items(),
                condition=UnlessCondition(detect_only),
            ),
        ]
    )
