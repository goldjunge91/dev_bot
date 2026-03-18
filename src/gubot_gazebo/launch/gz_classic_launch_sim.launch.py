import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    RegisterEventHandler,
    AppendEnvironmentVariable,
    SetEnvironmentVariable,
    ExecuteProcess,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    bringup_package_name = "gubot_one_bringup"
    gazebo_package_name = "gubot_gazebo"

    # Declare the 'world' argument
    # Note: For Ignition, world handling is slightly different, but ros_gz_sim accepts sdf file
    # We will pass the world file directly to gz_sim
    # Existing world 'obstacles.world' might need conversion to SDF or might work if compatible.
    # Generally, it's safer to launch an empty world or checking if obstacles.world is SDF compatible.
    # For now, let's assume we pass "-r <world_file>"
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(
            get_package_share_directory(gazebo_package_name),
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

    declare_launch_nerf_sim_ctrl_cmd = DeclareLaunchArgument(
        "launch_nerf_sim_controllers",
        default_value="true",
        description="Start tilt/shooter controllers in Gazebo Classic",
    )

    declare_launch_joystick_cmd = DeclareLaunchArgument(
        "launch_joystick",
        default_value="false",
        description="Start local joystick/teleop nodes",
    )

    declare_launch_twist_mux_cmd = DeclareLaunchArgument(
        "launch_twist_mux",
        default_value="false",
        description="Start local twist_mux node",
    )

    declare_zero_cmd_guard_cmd = DeclareLaunchArgument(
        "enable_zero_cmd_guard",
        default_value="true",
        description="Publish zero cmd_vel continuously to avoid unintended motion",
    )

    declare_gazebo_master_uri_cmd = DeclareLaunchArgument(
        "gazebo_master_uri",
        default_value="http://127.0.0.1:11346",
        description="Gazebo Classic master URI (change port if already in use)",
    )

    launch_nerf_sim_controllers = LaunchConfiguration("launch_nerf_sim_controllers")
    launch_joystick = LaunchConfiguration("launch_joystick")
    launch_twist_mux = LaunchConfiguration("launch_twist_mux")
    enable_zero_cmd_guard = LaunchConfiguration("enable_zero_cmd_guard")

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(bringup_package_name),
                    "launch",
                    "rsp.launch.py",
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
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
                    get_package_share_directory(bringup_package_name),
                    "launch",
                    "joystick.launch.py",
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
        condition=IfCondition(launch_joystick),
    )

    # Twist Mux
    twist_mux_params = os.path.join(
        get_package_share_directory(bringup_package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
        condition=IfCondition(launch_twist_mux),
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
        condition=IfCondition(launch_nerf_sim_controllers),
    )

    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
        output="screen",
        condition=IfCondition(launch_nerf_sim_controllers),
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
                    get_package_share_directory(bringup_package_name),
                    "config",
                    "view_bot.rviz",
            ),
        ],
        output="screen",
    )

    zero_cmd_guard = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            "-r",
            "20",
            "/diff_cont/cmd_vel_unstamped",
            "geometry_msgs/msg/Twist",
            "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}",
        ],
        output="screen",
        condition=IfCondition(enable_zero_cmd_guard),
    )

    return LaunchDescription(
        [
            world_arg,
            declare_use_sim_time_cmd,
            declare_launch_nerf_sim_ctrl_cmd,
            declare_launch_joystick_cmd,
            declare_launch_twist_mux_cmd,
            declare_zero_cmd_guard_cmd,
            declare_gazebo_master_uri_cmd,
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
            ),
            AppendEnvironmentVariable("GAZEBO_RESOURCE_PATH", "/usr/share/gazebo-11"),
            AppendEnvironmentVariable(
                "GAZEBO_RESOURCE_PATH",
                os.path.join(os.getcwd(), "src"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_RESOURCE_PATH",
                os.path.join(os.getcwd(), "install", "nerf_launch_system", "share"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_RESOURCE_PATH",
                os.path.join(os.getcwd(), "install", "gubot_one_description", "share"),
            ),
            SetEnvironmentVariable("GAZEBO_MASTER_URI", LaunchConfiguration("gazebo_master_uri")),
            # Force OpenGL 4.5 for Ogre 2 support via Software Rendering
            AppendEnvironmentVariable("MESA_GL_VERSION_OVERRIDE", "4.5"),
            AppendEnvironmentVariable("MESA_GLSL_VERSION_OVERRIDE", "450"),
            AppendEnvironmentVariable("GZ_TRANSPORT_RCVHWM", "1000"),
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
            zero_cmd_guard,
            rviz_node,
        ]
    )
