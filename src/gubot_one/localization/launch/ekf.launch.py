from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    package_name = "gubot_one"
    
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")

    ekf_config = PathJoinSubstitution([
        FindPackageShare(package_name),
        "localization",
        "config",
        "ekf.yaml"
    ])

    robot_localization_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_node",
        parameters=[ekf_config, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        robot_localization_node
    ])
