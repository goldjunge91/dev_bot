import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_gazebo"
    bringup_package_name = "gubot_one_bringup"

    use_rviz = LaunchConfiguration("use_rviz")
    launch_joystick = LaunchConfiguration("launch_joystick")
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

    cleanup_rogue_input_nodes = ExecuteProcess(
        cmd=[
            "bash",
            "-lc",
            "pkill -f 'nerf_teleop.py' || true; "
            "pkill -f 'nerf_joy.py' || true; "
            "pkill -f 'teleop_twist_joy.*teleop_node' || true; "
            "pkill -f 'joy_node' || true",
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
        launch_arguments={"use_sim_time": "true"}.items(),
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
        launch_arguments={
            "extra_gazebo_args": "--ros-args --params-file " + gazebo_params_file,
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
    )

    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
    )

    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
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

    return LaunchDescription(
        [
            declare_use_rviz_cmd,
            declare_launch_joystick_cmd,
            cleanup_rogue_input_nodes,
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
        ]
    )
