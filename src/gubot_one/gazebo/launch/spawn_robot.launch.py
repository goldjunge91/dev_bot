from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    package_name = "gubot_one"
    
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # 1. Spawn Robot Entity
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "gubot_one", "-z", "0.1"],
        output="screen",
    )

    # 2. Controller Launch (RSP + Spawners + Twist Mux)
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package_name), "controller", "launch", "controller.launch.py"])
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    # 3. EKF Localization
    ekf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package_name), "localization", "launch", "ekf.launch.py"])
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        spawn_entity,
        controller_launch,
        ekf_launch,
    ])
