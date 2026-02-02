import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_one"

    # Declare the 'world' argument
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(
            get_package_share_directory(package_name), "worlds", "obstacles.world"
        ),
        description="World to load",
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
                os.path.join(
                    get_package_share_directory(package_name), "launch", "rsp.launch.py"
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_ros2_control": "true",
            "integrated_mode": "true",
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

    # Gazebo
    gazebo_params_file = os.path.join(
        get_package_share_directory(package_name), "config", "gazebo_params.yaml"
    )
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
            "extra_gazebo_args": "--verbose --ros-args --params-file "
            + gazebo_params_file,
        }.items(),
    )

    # Spawn Entity - This MUST complete before controllers can start
    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic",
            "robot_description",
            "-entity",
            "gubot_one",
            "-timeout",
            "120",
        ],
        output="screen",
    )

    # Controller Spawners - Must wait for spawn_entity to complete
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

    # WICHTIG: Verzögerung der Controller bis spawn_entity fertig ist
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

    # Nerf Launcher Controllers - from nerf_standalone
    flywheel_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["flywheel_controller"],
        output="screen",
    )

    trigger_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller"],
        output="screen",
    )

    pusher_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller"],
        output="screen",
    )

    delayed_nerf_flywheel = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[flywheel_controller_spawner],
        )
    )

    delayed_nerf_trigger = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[trigger_controller_spawner],
        )
    )

    delayed_nerf_pusher = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[pusher_controller_spawner],
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

    # Launch mit korrekter Reihenfolge:
    # 1. Gazebo + RSP starten gleichzeitig
    # 2. spawn_entity startet (wartet intern auf /spawn_entity service)
    # 3. NACH spawn_entity: Controller starten
    return LaunchDescription(
        [
            world_arg,
            declare_use_sim_time_cmd,
            rsp,
            joystick,
            twist_mux,
            gazebo,
            spawn_entity,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_nerf_flywheel,
            delayed_nerf_trigger,
            delayed_nerf_pusher,
            delayed_nerf_arming,
            rviz_node,
        ]
    )
