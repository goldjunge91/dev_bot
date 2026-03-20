import os

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
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_one_bringup"

    # Declare the 'world' argument.
    # Pass the world file directly to Gazebo Classic.
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(
            get_package_share_directory("gubot_gazebo"),
            "worlds",
            "obstacles_classic.world",
        ),
        description="Path to the gazebo world file",
    )

    # Declare the 'use_sim_time' argument
    use_sim_time = LaunchConfiguration("use_sim_time")
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use sim time if true",
    )

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                # VORHER:
                # os.path.join(
                #     get_package_share_directory(package_name),
                #     "launch", "rsp.launch.py"
                # )
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "rsp_classic.launch.py",
                )
            ]
        ),
        # VORHER:
        # launch_arguments={
        #     "use_sim_time": use_sim_time,
        #     "use_ros2_control": "true",
        #     "integrated_mode": "true",
        #     "use_gazebo_classic": "true",
        # }.items(),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "integrated_mode": "true",
            "use_nerf_hardware": "true",
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
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
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
            "gubot_one_bringup",
            "-z",
            "0.1",
        ],
        output="screen",
    )

    # Controller Spawners - Must wait for spawn_entity to complete
    # In Ignition, we just wait for spawn.
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster"],
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
        arguments=["tilt_controller"],
        output="screen",
    )

    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
        output="screen",
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
                get_package_share_directory(package_name), "config", "view_bot.rviz"
            ),
        ],
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
            declare_use_sim_time_cmd,
            rsp,
            joystick,
            twist_mux,
            gazebo,
            spawn_entity,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_imu_broadcaster_spawner,
            delayed_nerf_tilt,
            delayed_nerf_shooter,
            delayed_nerf_arming,
            rviz_node,
        ]
    )
