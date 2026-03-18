"""
Robot State Publisher (Classic) Launch
=======================================
Lädt robot_classic.urdf.xacro – dedizierter Einstiegspunkt für Gazebo Classic.
Keine bedingten Guards, keine sim/hardware-Flags nötig.

Verwendung:
  ros2 launch gubot_one_bringup rsp_classic.launch.py
  ros2 launch gubot_one_bringup rsp_classic.launch.py use_sim_time:=true
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    pkg_path = os.path.join(get_package_share_directory("gubot_one_description"))
    xacro_file = os.path.join(pkg_path, "description", "robot_classic.urdf.xacro")

    robot_description_config = Command(["xacro ", xacro_file])

    params = {
        "robot_description": ParameterValue(robot_description_config, value_type=str),
        "use_sim_time": use_sim_time,
    }

    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[params],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use sim time if true",
            ),
            node_robot_state_publisher,
        ]
    )
