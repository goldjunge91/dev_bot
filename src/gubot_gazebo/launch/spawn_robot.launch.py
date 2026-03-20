import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_gazebo"
    description_package_name = "gubot_one_bringup"

    # Declare the 'use_sim_time' argument
    use_sim_time = LaunchConfiguration("use_sim_time")
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use sim time if true",
    )

    # Declare the 'use_rviz' argument (disabled by default on WSLg - no OpenGL support)
    use_rviz = LaunchConfiguration("use_rviz")
    launch_joystick = LaunchConfiguration("launch_joystick")
    declare_use_rviz_cmd = DeclareLaunchArgument(
        "use_rviz",
        default_value="false",
        description="Launch RViz2 (requires OpenGL support, disabled by default on WSLg)",
    )
    declare_launch_joystick_cmd = DeclareLaunchArgument(
        "launch_joystick",
        default_value="false",
        description="Start joystick/teleop/nerf_joy input pipeline",
    )

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(description_package_name),
                    "launch",
                    "rsp.launch.py",
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_ros2_control": "true",
            "integrated_mode": "true",
        }.items(),
    )

    # Joystick
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(description_package_name),
                    "launch",
                    "joystick.launch.py",
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
        condition=IfCondition(launch_joystick),
    )

    # Twist Mux
    twist_mux_params = os.path.join(
        get_package_share_directory(description_package_name),
        "config",
        "twist_mux.yaml",
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
    )

    # Spawn Entity
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "gubot_one_bringup",
            "-z",
            "0.1",
        ],
        output="screen",
    )

    # Robot GZ Bridge
    robot_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": os.path.join(
                    get_package_share_directory(package_name), "config", "robot_bridge.yaml"
                )
            }
        ],
        output="screen",
    )

    # Controller Spawners
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont", "--controller-manager-timeout", "60"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad", "--controller-manager-timeout", "60"],
    )

    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster", "--controller-manager-timeout", "60"],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[diff_drive_spawner],
        )
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_broad_spawner],
        )
    )

    delayed_imu_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[imu_broadcaster_spawner],
        )
    )

    # Nerf Launcher Controllers
    tilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller", "--controller-manager-timeout", "60"],
    )

    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller", "--controller-manager-timeout", "60"],
    )

    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller", "--controller-manager-timeout", "60"],
    )

    delayed_nerf_tilt = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[tilt_controller_spawner],
        )
    )

    delayed_nerf_shooter = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[shooter_controller_spawner],
        )
    )

    delayed_nerf_arming = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[arming_controller_spawner],
        )
    )

    # IMU Filter (Madgwick)
    imu_filter_params = os.path.join(
        get_package_share_directory(package_name), "config", "imu_filter.yaml"
    )
    imu_filter_node = Node(
        package="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        name="imu_filter",
        output="screen",
        parameters=[imu_filter_params],
        remappings=[
            ("/imu/data_raw", "/imu_broadcaster/imu"),
            ("/imu/data", "/imu/data"),
        ],
    )

    # RViz (disabled by default on WSLg due to GLX OpenGL context failures)
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(
                get_package_share_directory(description_package_name),
                "config",
                "view_bot.rviz",
            ),
        ],
        output="screen",
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        [
            declare_use_sim_time_cmd,
            declare_use_rviz_cmd,
            declare_launch_joystick_cmd,
            rsp,
            joystick,
            twist_mux,
            spawn_entity,
            robot_bridge,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_imu_broadcaster_spawner,
            imu_filter_node,
            rviz_node,
            delayed_nerf_tilt,
            delayed_nerf_shooter,
            delayed_nerf_arming,
        ]
    )
