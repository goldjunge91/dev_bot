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
    target_arg = LaunchConfiguration("target")
    allow_search = LaunchConfiguration("allow_search")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "detect_only",
                default_value="false",
                description="Nur Detektion (keine Bewegung des Roboters)",
            ),
            DeclareLaunchArgument(
                "target",
                default_value="",
                description='Name der Zielperson (z.B. "schatz" - leer = alle)',
            ),
            DeclareLaunchArgument(
                "allow_search",
                default_value="false",
                description="Ob der Roboter rotieren soll, wenn kein Gesicht gefunden wird",
            ),
            # --- SIMULATION ONLY ---
            # Hinweis: Der v4l2_camera_node wird absichtlich NICHT gestartet!
            # Die Kamerabilder kommen stattdessen aus Gazebo (über ros_gz_bridge)
            # auf dem Topic /camera/image_raw
            # 1. Face Detector
            # Abonniert /camera/image_raw (von Gazebo) und publiziert /face_detections
            Node(
                package="ball_tracker",
                executable="detect_face",
                parameters=[params_file],
                # In der Simulation heißt das Topic meist direkt /camera/image_raw
                remappings=[
                    ("/image_in", "/camera/image_raw"),
                    ("/image_out", "/image_out"),
                ],
            ),
            # 2. Face Follower
            # Abonniert /face_detections und steuert /cmd_vel und /nerf/tilt
            Node(
                package="ball_tracker",
                executable="follow_face",
                parameters=[
                    params_file,
                    {"target_person": target_arg, "allow_search": allow_search},
                ],
                remappings=[("/cmd_vel", "/cmd_vel")],
                condition=UnlessCondition(detect_only),
            ),
            # 3. Fire At Face (Schießt auf Ziel)
            Node(
                package="ball_tracker",
                executable="fire_at_face",
                parameters=[params_file, {"target_person": target_arg}],
                condition=UnlessCondition(detect_only),
            ),
        ]
    )
