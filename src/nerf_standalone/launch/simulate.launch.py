import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_nerf = get_package_share_directory("nerf_standalone")
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")

    # Declare the 'world' argument
    # world_arg = DeclareLaunchArgument(
    #     "world",
    #     default_value=os.path.join(
    #         get_package_share_directory(pkg_nerf), "worlds", "obstacles.world"
    #     ),
    #     description="World to load",
    # )

    # Process URDF
    xacro_file = os.path.join(pkg_nerf, "description", "urdf", "launcher.urdf.xacro")
    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {"robot_description": robot_description_config.toxml()}

    # Robot State Publisher
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "verbose": "true",
            # Required plugins for successful spawning
            "server_required_plugins": "libgazebo_ros_init.so libgazebo_ros_factory.so",
        }.items(),
    )

    # Spawn Entity
    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "nerf_launcher"],
        output="screen",
    )

    # RViz Config
    rviz_config = os.path.join(pkg_nerf, "config", "view.rviz")

    # RViz
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    # Spawner for Joint State Broadcaster
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    return LaunchDescription(
        [
            gazebo,
            node_robot_state_publisher,
            spawn_entity,
            joint_state_broadcaster_spawner,
            rviz,
        ]
    )
