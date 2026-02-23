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

    # Gazebo Sim (Ignition)
    # ros_gz_sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                )
            ]
        ),
        launch_arguments={
            "gz_args": ["-r -v 4 ", LaunchConfiguration("world")],
        }.items(),
    )

    # Spawn Entity
    # ros_gz_sim create
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "gubot_one",
            "-z",
            "0.1",
        ],
        output="screen",
    )

    # ROS GZ Bridge
    # Topics:
    # /clock (GZ->ROS)
    # /scan (GZ->ROS)
    # /camera/image_raw (GZ->ROS)
    # /camera/camera_info (GZ->ROS)
    # Note: ign_ros2_control handles joint states and commands.
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/imu_sensor/imu_data@sensor_msgs/msg/Imu[gz.msgs.IMU",
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
            bridge,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_imu_broadcaster_spawner,
            delayed_nerf_flywheel,
            delayed_nerf_trigger,
            delayed_nerf_pusher,
            delayed_nerf_arming,
            rviz_node,
        ]
    )
