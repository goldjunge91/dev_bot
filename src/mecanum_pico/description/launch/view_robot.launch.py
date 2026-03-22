# MIGRATION STATUS: COMPLETE (Sprint 3)
# view_robot.launch.py — standalone URDF visualisation in RViz.
# Ported from diffdrive_arduino/description/launch/view_robot.launch.py.
# Usage: ros2 launch mecanum_pico view_robot.launch.py

from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("mecanum_pico"), "urdf", "mecanum_robot.urdf.xacro"]
            ),
            " use_mock_hardware:=true",
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    rviz_config = PathJoinSubstitution(
        [FindPackageShare("mecanum_pico"), "rviz", "mecanum_pico.rviz"]
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    joint_state_publisher = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        output="screen",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=["-d", rviz_config],
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher,
        rviz_node,
    ])
