import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_nerf = get_package_share_directory("nerf_standalone")

    # Process URDF (with hardware flag)
    xacro_file = os.path.join(pkg_nerf, "description", "urdf", "launcher.urdf.xacro")

    # Process xacro with use_hardware=true
    robot_description_config = xacro.process_file(
        xacro_file, mappings={"use_hardware": "true"}
    )
    robot_description = {"robot_description": robot_description_config.toxml()}

    # Robot State Publisher
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": False}],
    )

    # Controller Manager (ros2_control_node)
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            robot_description,
            os.path.join(pkg_nerf, "config", "controllers.yaml"),
            {"use_sim_time": False},
        ],
        output="screen",
        emulate_tty=True,  # Improved console output
    )

    # Spawners
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    trigger_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    flywheel_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "flywheel_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    pusher_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    arming_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # High-level Control Node
    nerf_control = Node(
        package="nerf_standalone",
        executable="nerf_control_node",
        output="screen",
    )

    return LaunchDescription(
        [
            node_robot_state_publisher,
            controller_manager,
            joint_state_broadcaster,
            trigger_controller,
            flywheel_controller,
            pusher_controller,
            arming_controller,
            nerf_control,
        ]
    )
