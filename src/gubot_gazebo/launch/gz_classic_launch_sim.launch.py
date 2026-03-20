import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    ExecuteProcess,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_gazebo"
    bringup_package_name = "gubot_one_bringup"

    use_rviz = LaunchConfiguration("use_rviz")
    launch_joystick = LaunchConfiguration("launch_joystick")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    gui = LaunchConfiguration("gui")
    declare_use_rviz_cmd = DeclareLaunchArgument(
        "use_rviz",
        default_value="true",
        description="Launch RViz2",
    )
    declare_launch_joystick_cmd = DeclareLaunchArgument(
        "launch_joystick",
        default_value="false",
        description="Start joystick/teleop/nerf_joy input pipeline",
    )
    declare_use_nerf_hardware_cmd = DeclareLaunchArgument(
        "use_nerf_hardware",
        default_value="true",
        description="Enable NERF launcher links/controllers in Classic simulation",
    )
    declare_gui_cmd = DeclareLaunchArgument(
        "gui",
        default_value="true",
        description="Set to false to run Gazebo Classic headless",
    )

    cleanup_rogue_input_nodes = ExecuteProcess(
        cmd=[
            "bash",
            "-lc",
            # VORHER:
            # "pkill -f 'nerf_teleop.py' || true; "
            # "pkill -f 'nerf_joy.py' || true; "
            # "pkill -f 'teleop_twist_joy.*teleop_node' || true; "
            # "pkill -f 'joy_node' || true",
            "pkill -f '[n]erf_teleop.py' || true; "
            "pkill -f '[n]erf_joy.py' || true; "
            "pkill -f 'teleop_twist_joy.*[t]eleop_node' || true; "
            "pkill -f '[j]oy_node' || true; "
            "pkill -f '[g]zserver' || true; "
            "pkill -f '[g]zclient' || true",
        ],
        output="screen",
        condition=UnlessCondition(launch_joystick),
    )

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(bringup_package_name),
                    "launch",
                    "rsp_classic.launch.py",
                )
            ]
        ),
        # VORHER:
        # launch_arguments={"use_sim_time": "true"}.items(),
        launch_arguments={
            "use_sim_time": "true",
            "integrated_mode": "true",
            "use_nerf_hardware": use_nerf_hardware,
        }.items(),
    )

    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(bringup_package_name),
                    "launch",
                    "joystick.launch.py",
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
        condition=IfCondition(launch_joystick),
    )

    twist_mux_params = os.path.join(
        get_package_share_directory(bringup_package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
    )

    gazebo_params_file = os.path.join(
        get_package_share_directory(package_name),
        "config",
        "gazebo_params.yaml",
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
        # VORHER:
        # launch_arguments={
        #     "extra_gazebo_args": "--ros-args --params-file " + gazebo_params_file,
        # }.items(),
        launch_arguments={
            "extra_gazebo_args": "--ros-args --params-file " + gazebo_params_file,
            "gui": gui,
        }.items(),
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic",
            "robot_description",
            "-entity",
            "gubot_one_bringup",
        ],
        output="screen",
    )

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

    tilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller"],
        condition=IfCondition(use_nerf_hardware),
    )

    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
        condition=IfCondition(use_nerf_hardware),
    )

    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
        condition=IfCondition(use_nerf_hardware),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(
                get_package_share_directory(bringup_package_name),
                "config",
                "view_bot.rviz",
            ),
        ],
        output="screen",
        condition=IfCondition(use_rviz),
    )

    delayed_main_actions = TimerAction(
        period=1.5,
        actions=[
            rsp,
            joystick,
            twist_mux,
            gazebo,
            spawn_entity,
            diff_drive_spawner,
            joint_broad_spawner,
            tilt_controller_spawner,
            shooter_controller_spawner,
            arming_controller_spawner,
            rviz_node,
        ],
    )

    return LaunchDescription(
        [
            declare_use_rviz_cmd,
            declare_launch_joystick_cmd,
            declare_use_nerf_hardware_cmd,
            declare_gui_cmd,
            cleanup_rogue_input_nodes,
            delayed_main_actions,
        ]
    )
