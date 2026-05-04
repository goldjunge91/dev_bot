import os

import launch # Added this line
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    RegisterEventHandler,
    AppendEnvironmentVariable,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression # Modified this line

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_one"

    # Declare the 'world' argument
    # Note: For Ignition, world handling is slightly different, but ros_gz_sim accepts sdf file
    # We will pass the world file directly to gz_sim
    # Existing world 'obstacles.world' might need conversion to SDF or might work if compatible.
    # Generally, it's safer to launch an empty world or checking if obstacles.world is SDF compatible.
    # For now, let's assume we pass "-r <world_file>"
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(
            get_package_share_directory(package_name),
            "worlds",
            "obstacles_classic.world",
        ),
        description="Path to the gazebo world file",
    )



    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(
                        package_name), "launch", "rsp.launch.py"
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": "true",
            "use_ros2_control": "true",
            "integrated_mode": "true",
            "use_gazebo_classic": "true",
        }.items(),
    )

    # Joystick
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "joystick.launch.py",
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
    )

    # Twist Mux
    twist_mux_params = os.path.join(
        get_package_share_directory(package_name), "config", "twist_mux.yaml"
    )

    # Remapping Logic based on drive_type
    # Note: We use dynamic Python inside the launch function or substitutions
    # Using LaunchConfiguration in remappings requires care
    cmd_vel_out = "/mecanum_cont/cmd_vel_unstamped"  # Korrekter Topic-Name des mecanum_drive_controller

    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", cmd_vel_out)],
    )

    # Gazebo Sim (Classic)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("gazebo_ros"),
                    "launch",
                    "gazebo.launch.py",
                )
            ]
        ),
        launch_arguments={
            "world": LaunchConfiguration("world"),
            "verbose": "true",
        }.items(),
    )

    # Spawn Entity
    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic",
            "robot_description",
            "-entity",
            "gubot_one",
            "-z",
            "0.2",
        ],
        output="screen",
    )

    # Controller Spawners - Must wait for spawn_entity to complete
    # In Ignition, we just wait for spawn.
    mecanum_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["mecanum_cont"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster"],
    )

    delayed_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[mecanum_drive_spawner],
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
    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
        output="screen",
    )

    tilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller"],
        output="screen",
    )

    delayed_nerf_shooter = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[shooter_controller_spawner],
        )
    )

    delayed_nerf_tilt = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[tilt_controller_spawner],
        )
    )

    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
        output="screen",
    )

    delayed_nerf_arming = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[arming_controller_spawner],
        )
    )

    # RViz
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(
                get_package_share_directory(
                    package_name), "config", "view_bot.rviz"
            ),
        ],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription(
        [
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
            ),
            # Force OpenGL 4.5 for Ogre 2 support via Software Rendering
            AppendEnvironmentVariable("MESA_GL_VERSION_OVERRIDE", "4.5"),
            AppendEnvironmentVariable("MESA_GLSL_VERSION_OVERRIDE", "450"),
            AppendEnvironmentVariable("GZ_TRANSPORT_RCVHWM", "1000"),
            world_arg,
            rsp,
            joystick,
            twist_mux,
            gazebo,
            spawn_entity,
            delayed_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_imu_broadcaster_spawner,
            delayed_nerf_shooter,
            delayed_nerf_tilt,
            delayed_nerf_arming,
            rviz_node,
        ]
    )
