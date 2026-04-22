import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    AppendEnvironmentVariable,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():

    package_name = "gubot_one"

    # 1. Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), "launch", "rsp.launch.py"
        )]),
        launch_arguments={
            "use_sim_time": "true",
            "use_ros2_control": "true",
            "integrated_mode": "true",
            "drive_type": LaunchConfiguration("drive_type"),
            # ALT: use_nerf_hardware wurde nicht übergeben → default 'true' aus rsp.launch.py
            # Das führte dazu dass Nerf-Joints immer im GazeboSimSystem registriert wurden
            "use_nerf_hardware": "false",
        }.items(),
    )

    # 2. Joystick
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), "launch", "joystick.launch.py"
        )]),
        launch_arguments={"use_sim_time": "true"}.items(),
    )

    # 3. Twist Mux
    twist_mux_params = os.path.join(
        get_package_share_directory(package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        # ALT: remappings=[("/cmd_vel_out", "/mecanum_cont/reference_unstamped")],
        remappings=[("/cmd_vel_out", "/mecanum_cont/cmd_vel_unstamped")],
    )

    # 4. World
    default_world = os.path.join(
        get_package_share_directory(package_name), "worlds", "obstacles.world"
    )
    world = LaunchConfiguration("world")

    # 5. Gazebo (Ignition)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
        )]),
        launch_arguments={
            "gz_args": ["-r -v4 ", world],
            "on_exit_shutdown": "true",
        }.items(),
    )

    # 6. Spawn Entity
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "gubot_one", "-z", "0.1"],
        output="screen",
    )

    # 7-12. Controller Spawner
    # ign_ros2_control laedt Controller aus my_controllers.yaml automatisch beim
    # Plugin-Start. Die Hardware-Interfaces werden aber erst registriert wenn
    # Ignition das Modell vollstaendig geladen hat. Spawner die sofort starten
    # treffen auf noch-nicht-bereite Hardware → configure schlaegt fehl.
    # Fix: TimerAction(5s) gibt ign_ros2_control genuegend Zeit.
    enable = LaunchConfiguration("enable_ros2_controllers")

    drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["mecanum_cont"],
        condition=IfCondition(enable),
    )
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        # ALT: arguments=["joint_broad"],
        arguments=["joint_state_broadcaster"],
        condition=IfCondition(enable),
    )
    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster"],
        condition=IfCondition(enable),
    )
    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
        output="screen",
        condition=IfCondition(enable),
    )
    tilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller"],
        output="screen",
        condition=IfCondition(enable),
    )
    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
        output="screen",
        condition=IfCondition(enable),
    )

    delayed_spawners = TimerAction(
        period=5.0,
        actions=[
            drive_spawner,
            joint_broad_spawner,
            imu_broadcaster_spawner,
            shooter_controller_spawner,
            tilt_controller_spawner,
            arming_controller_spawner,
        ],
    )

    # 13. ROS <-> GZ Bridge
    bridge_params = os.path.join(
        get_package_share_directory(package_name), "config", "gz_bridge.yaml"
    )
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_params}"],
        output="screen",
    )

    # 14. Image Bridge
    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"],
        output="screen",
    )

    # 15. RViz
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(
            get_package_share_directory(package_name), "config", "view_bot.rviz"
        )],
        output="screen",
    )

    return LaunchDescription([
        AppendEnvironmentVariable(
            "IGN_GAZEBO_RESOURCE_PATH",
            os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
        ),
        AppendEnvironmentVariable(
            "GAZEBO_MODEL_PATH",
            os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
        ),
        AppendEnvironmentVariable("MESA_GL_VERSION_OVERRIDE", "4.5"),
        AppendEnvironmentVariable("MESA_GLSL_VERSION_OVERRIDE", "450"),
        
        # --- GPU Acceleration für WSL (Erzwingt Nvidia bei Hybrid-Systemen) ---
        SetEnvironmentVariable("LIBGL_ALWAYS_SOFTWARE", "0"),
        SetEnvironmentVariable("GALLIUM_DRIVER", "d3d12"),
        # Da du beides hast, zwingen wir WSL hier, die starke Nvidia-GPU zu nutzen!
        SetEnvironmentVariable("MESA_D3D12_DEFAULT_ADAPTER_NAME", "NVIDIA"),
        
        AppendEnvironmentVariable("QT_QPA_PLATFORM", "xcb"),
        AppendEnvironmentVariable("GZ_TRANSPORT_RCVHWM", "1000"),
        DeclareLaunchArgument("use_sim_time", default_value="true",
                              description="Use sim time if true"),
        DeclareLaunchArgument("world", default_value=default_world,
                              description="World to load"),
        DeclareLaunchArgument("enable_ros2_controllers", default_value="true",
                              description="Spawn ros2_control controllers"),
        DeclareLaunchArgument("drive_type", default_value="mecanum",
                              description="Drive type: diffdrive or mecanum"),
        # correct order is importend
        rsp,
        joystick,
        twist_mux,
        gazebo,
        spawn_entity,
        ros_gz_bridge,
        ros_gz_image_bridge,
        rviz_node,
        delayed_spawners,
    ])
