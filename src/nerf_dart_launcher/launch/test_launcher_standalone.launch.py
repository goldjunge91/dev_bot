"""Standalone Gazebo simulation for testing Nerf Launcher in isolation."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_nerf = get_package_share_directory('nerf_dart_launcher')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    
    # Process URDF
    xacro_file = os.path.join(pkg_nerf, 'urdf', 'nerf_launcher_standalone.urdf.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()
    
    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )
    
    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={
            'verbose': 'true',
            'server_required_plugins': 'libgazebo_ros_init.so libgazebo_ros_factory.so libgazebo_ros_force_system.so'
        }.items()
    )
    
    # Spawn entity
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'nerf_launcher'
        ],
        output='screen'
    )
    
    # Controller Spawners (delayed until after entity spawn)
    flywheel_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['flywheel_controller', 
                   '--param-file', os.path.join(pkg_nerf, 'config', 'nerf_controllers.yaml')],
        output='screen'
    )
    
    trigger_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['trigger_controller',
                   '--param-file', os.path.join(pkg_nerf, 'config', 'nerf_controllers.yaml')],
        output='screen'
    )
    
    pusher_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['pusher_controller',
                   '--param-file', os.path.join(pkg_nerf, 'config', 'nerf_controllers.yaml')],
        output='screen'
    )
    
    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )
    
    # Delayed spawners
    delayed_joint_broad = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_broad_spawner],
        )
    )
    
    delayed_flywheel = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[flywheel_spawner],
        )
    )
    
    delayed_trigger = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[trigger_spawner],
        )
    )
    
    delayed_pusher = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[pusher_spawner],
        )
    )
    
    # RViz
    rviz_config = os.path.join(pkg_nerf, 'config', 'nerf_launcher_view.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config] if os.path.exists(rviz_config) else [],
        parameters=[{'use_sim_time': True}]
    )
    
    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_entity,
        delayed_joint_broad,
        delayed_flywheel,
        delayed_trigger,
        delayed_pusher,
        rviz
    ])
