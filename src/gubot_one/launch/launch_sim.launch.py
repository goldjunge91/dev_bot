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

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name), "launch", "rsp.launch.py"
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true", "use_ros2_control": "true"}.items(),
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
            "extra_gazebo_args": "--ros-args --params-file " + gazebo_params_file,
        }.items(),
    )

    # Spawn Entity - This MUST complete before controllers can start
    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "gubot_one"],
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

    # Nerf Launcher Controllers - auch verzögern
    nerf_controllers = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("nerf_dart_launcher"),
                    "launch",
                    "nerf_controllers.launch.py",
                )
            ]
        ),
    )

    delayed_nerf_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[nerf_controllers],
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
            rsp,
            joystick,
            twist_mux,
            gazebo,
            spawn_entity,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_nerf_controllers,
            rviz_node,
        ]
    )
