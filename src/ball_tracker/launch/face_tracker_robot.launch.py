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
    target_arg = LaunchConfiguration("target")

    return LaunchDescription(
        [
            # --- Argumente zur Steuerung ---
            # "detect_only": Wenn true, bewegt sich der Roboter NICHT.
            # Gut zum Testen der Kamera und Gesichtserkennung, ohne dass der Roboter wegfährt.
            DeclareLaunchArgument(
                "detect_only",
                default_value="false",
                description="Nur Detektion (keine Bewegung des Roboters)",
            ),
            # "follow_only": Wenn true, startet KEINE Kamera/Erkennung.
            # Erwartet, dass /face_detections bereits von woanders kommen (z.B. Rosbag oder anderer Node).
            DeclareLaunchArgument(
                "follow_only",
                default_value="false",
                description="Nur Verfolgung (keine Bildverarbeitung - erwartet /face_detections)",
            ),
            # "target": Filtert auf eine spezifische Person.
            # - Leer ("") = Reagiert auf ALLE bekannten Gesichter.
            # - Name (z.B. "marco") = Reagiert NUR, wenn "marco" erkannt wird.
            #   Alle anderen (z.B. "schatz" oder Unbekannte) werden ignoriert.
            DeclareLaunchArgument(
                "target",
                default_value="schatz",
                description='Name der Zielperson (z.B. "schatz", "marco" - leer = alle)',
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
                        "pixel_format": "YUYV",
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
                parameters=[params_file, {"target_person": target_arg}],
                remappings=[("/cmd_vel", "/cmd_vel")],
                condition=UnlessCondition(detect_only),
            ),
            # 4. Nerf Hardware Control
            # Steuert Flywheels und Pusher
            Node(
                package="nerf_standalone",
                executable="nerf_control_node",
                output="screen",
            ),
            # 5. Fire At Face
            # Feuert, wenn Ziel zentriert und nah genug
            Node(
                package="ball_tracker",
                executable="fire_at_face",
                parameters=[params_file, {"target_person": target_arg}],
                condition=UnlessCondition(detect_only),
            ),
        ]
    )
