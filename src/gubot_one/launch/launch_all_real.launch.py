import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition


def generate_launch_description():
    package_name = "gubot_one"

    # Arguments
    launch_lidar = LaunchConfiguration("launch_lidar")
    launch_camera = LaunchConfiguration("launch_camera")

    launch_lidar_arg = DeclareLaunchArgument(
        "launch_lidar",
        default_value="false",  # Default to false as user reported no lidar
        description="Whether to launch the RPLidar",
    )

    launch_camera_arg = DeclareLaunchArgument(
        "launch_camera",
        default_value="false",  # Default to false as user reported broken camera
        description="Whether to launch the USB Camera",
    )

    # Launch the robot base (State Publisher, Controller Manager, Hardware Interfaces, Twist Mux)
    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "launch_robot.launch.py",
                )
            ]
        )
    )

    # Launch the RPLidar
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "rplidar.launch.py",
                )
            ]
        ),
        condition=IfCondition(launch_lidar),
    )

    # Launch the Camera
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "real_camera.launch.py",
                )
            ]
        ),
        condition=IfCondition(launch_camera),
    )

    return LaunchDescription(
        [launch_lidar_arg, launch_camera_arg, base_launch, lidar_launch, camera_launch]
    )
