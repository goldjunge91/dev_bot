"""Launch Robot State Publisher for Gazebo Classic."""

import os
import re
import subprocess

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node


def _create_robot_state_publisher_node(context):
    """Create robot_state_publisher node with resolved xacro content."""
    use_sim_time_value = LaunchConfiguration("use_sim_time").perform(context)
    integrated_mode_value = LaunchConfiguration("integrated_mode").perform(context)
    use_nerf_hardware_value = LaunchConfiguration("use_nerf_hardware").perform(context)

    pkg_path = os.path.join(get_package_share_directory("gubot_one_description"))
    xacro_file = os.path.join(pkg_path, "description", "robot_classic.urdf.xacro")

    # VORHER:
    # robot_description_config = Command(
    #     [
    #         "xacro ",
    #         xacro_file,
    #         " integrated_mode:=",
    #         integrated_mode,
    #         " use_nerf_hardware:=",
    #         use_nerf_hardware,
    #     ]
    # )
    # Workaround: gazebo_ros2_control scheitert teils beim Parsen von
    # mehrzeiligem robot_description-Override. Daher URDF auf eine Zeile glätten.
    xacro_command = [
        "xacro",
        xacro_file,
        f"integrated_mode:={integrated_mode_value}",
        f"use_nerf_hardware:={use_nerf_hardware_value}",
    ]
    xacro_result = subprocess.run(
        xacro_command,
        capture_output=True,
        text=True,
        check=False,
    )
    if xacro_result.returncode != 0:
        raise RuntimeError(
            "xacro fehlgeschlagen in rsp_classic.launch.py:\n"
            f"Command: {' '.join(xacro_command)}\n"
            f"stderr:\n{xacro_result.stderr}"
        )

    # VORHER:
    # robot_description = " ".join(xacro_result.stdout.splitlines())
    robot_description = xacro_result.stdout
    robot_description = re.sub(r"<\?xml[^>]*\?>", "", robot_description)
    robot_description = re.sub(r"<!--.*?-->", "", robot_description, flags=re.DOTALL)
    robot_description = " ".join(robot_description.split())

    params = {
        "robot_description": robot_description,
        "use_sim_time": use_sim_time_value.lower() == "true",
    }

    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[params],
    )

    return [node_robot_state_publisher]


def generate_launch_description():
    # VORHER:
    # use_sim_time = LaunchConfiguration("use_sim_time")
    # use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "integrated_mode",
                default_value="false",
                description="Enable integrated mode if true",
            ),
            DeclareLaunchArgument(
                "use_nerf_hardware",
                default_value="true",
                description="Enable NERF hardware interfaces if true",
            ),
            OpaqueFunction(function=_create_robot_state_publisher_node),
        ]
    )
