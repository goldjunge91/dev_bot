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

    # UDP Receiver Node (ersetzt v4l2_camera)
    udp_receiver_node = Node(
        package="ball_tracker",
        executable="udp_cam_receiver",
        name="udp_cam_receiver",
        parameters=[{"port": 9999}],
        remappings=[("/image_raw", "/image_raw")],
    )

    # Face Detector (Code bleibt gleich!)
    detect_node = Node(
        package="ball_tracker",
        executable="detect_face",
        parameters=[params_file],
        remappings=[("/image_in", "/image_raw")],  # Input kommt vom UDP Receiver
        condition=UnlessCondition(follow_only),
    )

    # Face Follower
    follow_node = Node(
        package="ball_tracker",
        executable="follow_face",
        parameters=[params_file],
        remappings=[("/cmd_vel", "/cmd_vel")],
        condition=UnlessCondition(detect_only),
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
            detect_node,
            follow_node,
        ]
    )
