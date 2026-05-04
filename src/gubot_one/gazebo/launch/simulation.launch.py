import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    package_name = "gubot_one"

    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(get_package_share_directory(package_name), "gazebo", "worlds", "obstacles.world"),
        description="Ignition Gazebo World File"
    )
    
    use_nerf_hardware_arg = DeclareLaunchArgument(
        "use_nerf_hardware",
        default_value="true",
        description="Enable nerf hardware if true",
    )

    world = LaunchConfiguration("world")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    use_rviz = LaunchConfiguration("use_rviz", default="true")

    # 0. RViz
    rviz_config = os.path.join(get_package_share_directory(package_name), "description", "rviz", "main.rviz")
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(use_rviz)
    )

    # 1. Gazebo (Ignition)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={"gz_args": ["-r -v4 ", world], "on_exit_shutdown": "true"}.items(),
    )

    # 2. Gazebo Bridge
    gz_bridge_config = os.path.join(get_package_share_directory(package_name), "gazebo", "config", "gz_bridge.yaml")
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        parameters=[{"config_file": gz_bridge_config}],
    )

    # 3. Image Bridge
    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"],
        output="screen",
    )

    # 4. Spawn Robot
    spawn_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([get_package_share_directory(package_name), "gazebo", "launch", "spawn_robot.launch.py"])
        ),
        launch_arguments={"use_nerf_hardware": use_nerf_hardware}.items(),
    )

    return LaunchDescription([
        world_arg,
        use_nerf_hardware_arg,
        DeclareLaunchArgument("use_rviz", default_value="true", description="Start RViz"),
        gz_sim,
        gz_bridge,
        ros_gz_image_bridge,
        spawn_robot,
        rviz_node
    ])
