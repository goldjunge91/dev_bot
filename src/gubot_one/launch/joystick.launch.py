from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
import launch.conditions as if_condition

import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")

    launch_joy_node = LaunchConfiguration("launch_joy_node")

    joy_params = os.path.join(
        get_package_share_directory("gubot_one"), "config", "joystick.yaml"
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
        parameters=[joy_params, {"use_sim_time": use_sim_time}],
        condition=if_condition.IfCondition(launch_joy_node),
    )

    teleop_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        name="teleop_node",
        parameters=[joy_params, {"use_sim_time": use_sim_time}],
        remappings=[("/cmd_vel", "/cmd_vel_joy")],
    )

    # twist_stamper = Node(
    #         package='twist_stamper',
    #         executable='twist_stamper',
    #         parameters=[{'use_sim_time': use_sim_time}],
    #         remappings=[('/cmd_vel_in','/diff_cont/cmd_vel_unstamped'),
    #                     ('/cmd_vel_out','/diff_cont/cmd_vel')]
    #      )

    nerf_joy_node = Node(
        package="gubot_one",
        executable="nerf_joy.py",
        name="nerf_joy",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use sim time if true",
            ),
            DeclareLaunchArgument(
                "launch_joy_node",
                default_value="true",
                description="Whether to run joy_node locally",
            ),
            joy_node,
            teleop_node,
            nerf_joy_node,
            # twist_stamper
        ]
    )
