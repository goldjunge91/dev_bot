"""Launch file for Nerf Launcher with Serial Bridge."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")
    serial_port = LaunchConfiguration("serial_port")
    baud_rate = LaunchConfiguration("baud_rate")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="",
                description="Namespace for nerf launcher node",
            ),
            DeclareLaunchArgument(
                "serial_port",
                default_value="/dev/ttyACM0",
                description="Serial port for Arduino Pro Micro",
            ),
            DeclareLaunchArgument(
                "baud_rate",
                default_value="115200",
                description="Serial baud rate",
            ),
            Node(
                package="nerf_dart_launcher",
                executable="nerf_launcher_node",
                namespace=namespace,
                name="nerf_launcher",
                output="screen",
                parameters=[
                    {"serial_port": serial_port},
                    {"baud_rate": baud_rate},
                ],
            ),
        ]
    )
