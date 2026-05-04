import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    package_name = "gubot_one"
    
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")
    use_ros2_control = LaunchConfiguration("use_ros2_control", default="true")

    # 1. Load URDF (Robot State Publisher)
    load_urdf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package_name), "description", "launch", "load_urdf.launch.py"])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_ros2_control": use_ros2_control,
        }.items(),
    )

    # 2. Twist Mux
    twist_mux_config = PathJoinSubstitution([
        FindPackageShare(package_name), "controller", "config", "twist_mux.yaml"
    ])
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_config, {"use_sim_time": use_sim_time}],
        remappings=[("/cmd_vel_out", "/cmd_vel")],
    )

    # 3. Controller Spawners
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    mecanum_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["mecanum_drive_controller"],
    )

    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster"],
    )

    # Delay spawners to ensure controller_manager is ready
    delayed_joint_state_spawner = TimerAction(period=2.0, actions=[joint_state_broadcaster_spawner])
    delayed_mecanum_spawner = TimerAction(period=3.0, actions=[mecanum_drive_controller_spawner])
    delayed_imu_spawner = TimerAction(period=4.0, actions=[imu_broadcaster_spawner])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("use_ros2_control", default_value="true"),
        load_urdf,
        twist_mux,
        delayed_joint_state_spawner,
        delayed_mecanum_spawner,
        delayed_imu_spawner,
    ])
