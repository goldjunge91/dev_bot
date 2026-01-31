import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    # Get configuration file
    pkg_path = get_package_share_directory('nerf_dart_launcher')
    controller_params_file = os.path.join(pkg_path, 'config', 'nerf_controllers.yaml')

    # Spawners
    # Note: We pass the parameter file directly to the spawner!
    # This allows adding new controllers to the running controller_manager
    # with their specific configuration.
    
    flywheel_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["flywheel_controller", "--param-file", controller_params_file],
    )

    trigger_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller", "--param-file", controller_params_file],
    )

    pusher_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller", "--param-file", controller_params_file],
    )

    return LaunchDescription([
        flywheel_spawner,
        trigger_spawner,
        pusher_spawner,
    ])
