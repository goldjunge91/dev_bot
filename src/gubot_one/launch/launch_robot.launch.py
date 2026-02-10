import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
    DeclareLaunchArgument,
    GroupAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.conditions import IfCondition

from launch_ros.actions import Node


def generate_launch_description():
    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name = "gubot_one"  # <--- CHANGE ME

    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name), "launch", "rsp.launch.py"
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": "false",
            "use_ros2_control": "true",
            "integrated_mode": "true",
            "use_nerf_hardware": use_nerf_hardware,
        }.items(),
    )

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
        launch_arguments={"use_sim_time": "false", "launch_joy_node": "false"}.items(),
    )

    twist_mux_params = os.path.join(
        get_package_share_directory(package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
    )

    pkg_path = os.path.join(get_package_share_directory(package_name))
    xacro_file = os.path.join(pkg_path, "description", "robot.urdf.xacro")
    robot_description = Command(
        [
            "xacro ",
            xacro_file,
            " use_ros2_control:=true",
            " sim_mode:=false",
            " integrated_mode:=true",
            " use_nerf_hardware:=",
            use_nerf_hardware,
        ]
    )

    controller_params_file = os.path.join(
        get_package_share_directory(package_name), "config", "my_controllers.yaml"
    )

    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[{"robot_description": robot_description}, controller_params_file],
    )

    delayed_controller_manager = TimerAction(period=3.0, actions=[controller_manager])

    # --- Spawner daisy-chaining to prevent "thundering herd" on DDS ---
    # Chain: diff_cont -> joint_broad -> trigger -> flywheel -> pusher -> arming -> control_node
    # We use OnProcessExit because spawners exit after successful loading.

    from launch.event_handlers import OnProcessExit

    # 1. Diff Drive (starts after controller_manager starts)
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner],
        )
    )

    # 2. Joint Broadcaster (starts after diff_drive exits)
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=diff_drive_spawner,
            on_exit=[joint_broad_spawner],
        )
    )

    # 3. Nerf Trigger (starts after joint_broad exits)
    nerf_trigger_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller"],
        output="screen",
    )

    delayed_nerf_trigger = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_broad_spawner,
            on_exit=[nerf_trigger_spawner],
        )
    )

    # 4. Nerf Flywheel (starts after trigger exits)
    nerf_flywheel_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["flywheel_controller"],
        output="screen",
    )

    delayed_nerf_flywheel = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_trigger_spawner,
            on_exit=[nerf_flywheel_spawner],
        )
    )

    # 5. Nerf Pusher (starts after flywheel exits)
    nerf_pusher_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller"],
        output="screen",
    )

    delayed_nerf_pusher = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_flywheel_spawner,
            on_exit=[nerf_pusher_spawner],
        )
    )

    # 6. Nerf Arming (starts after pusher exits)
    nerf_arming_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
        output="screen",
    )

    delayed_nerf_arming = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_pusher_spawner,
            on_exit=[nerf_arming_spawner],
        )
    )

    # 7. Nerf Control Node (starts after arming exits)
    nerf_control = Node(
        package="nerf_standalone",
        executable="nerf_control_node",
        output="screen",
    )

    delayed_nerf_control = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_arming_spawner,
            on_exit=[nerf_control],
        )
    )

    nerf_group = GroupAction(
        condition=IfCondition(use_nerf_hardware),
        actions=[
            delayed_nerf_trigger,
            delayed_nerf_flywheel,
            delayed_nerf_pusher,
            delayed_nerf_arming,
            delayed_nerf_control,
        ],
    )

    # Launch them all!
    # Only need to return the first trigger (delayed_diff_drive_spawner)
    # The rest triggers automatically via events.
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_nerf_hardware",
                default_value="false",
                description="Enable Nerf hardware if true",
            ),
            rsp,
            joystick,
            twist_mux,
            delayed_controller_manager,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            nerf_group,
        ]
    )
