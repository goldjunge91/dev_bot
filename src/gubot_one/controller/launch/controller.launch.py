"""
Controller Launch
=================
Startet robot_state_publisher, twist_mux, den controller_manager (nur echte
Hardware) und alle ros2_control Spawner.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_controller/launch/controller.launch.py
)
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit, OnProcessIO
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = "gubot_one"

    use_sim_time = LaunchConfiguration("use_sim_time", default="false")
    use_ros2_control = LaunchConfiguration("use_ros2_control", default="true")
    use_nerf_hardware = LaunchConfiguration(
        "use_nerf_hardware", default="true")
    use_camera = LaunchConfiguration("use_camera", default="true")
    auto_arm = LaunchConfiguration("auto_arm", default="false")

    # 1. Load URDF (Robot State Publisher)
    # controller_config wird mit Standardpfad geladen (überschreibbar)
    load_urdf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare(
                    package_name), "description", "launch", "load_urdf.launch.py"
            ])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_ros2_control": use_ros2_control,
            "use_nerf_hardware": use_nerf_hardware,
            "use_camera": use_camera,
        }.items(),
    )

    # 2. Twist Mux
    twist_mux_config = PathJoinSubstitution([
        FindPackageShare(
            package_name), "controller", "config", "twist_mux.yaml"
    ])
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_config],
        # /cmd_vel ist der gemeinsame Topic-Vertrag (Sim + Real): der Controller
        # wird per Remap auf cmd_vel gelegt — in der Sim durch das gz-Plugin
        # (ros2_control_gazebo_ign_fortress.xacro), auf echter Hardware durch
        # die Remappings am ros2_control_node unten.
        remappings=[("/cmd_vel_out", "/cmd_vel")],
    )

    # 3. Controller Manager (ros2_control_node) — NUR echte Hardware.
    # In der Simulation startet gz_ros2_control den Manager im Gazebo-Prozess.
    # robot_description kommt per Topic vom robot_state_publisher (load_urdf);
    # die Remappings spiegeln exakt die <ros>-Remappings des Sim-Plugins,
    # damit Sim und Real denselben Topic-Vertrag haben (Referenz-Pattern
    # rosbot_controller/launch/controller.launch.py).
    controller_config = PathJoinSubstitution([
        FindPackageShare(
            package_name), "controller", "config", "controllers.yaml"
    ])
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[controller_config],
        remappings=[
            ("mecanum_drive_controller/cmd_vel_unstamped", "cmd_vel"),
            ("mecanum_drive_controller/odom", "odometry/wheels"),
            (
                "mecanum_drive_controller/transition_event",
                "_mecanum_drive_controller/transition_event",
            ),
            ("imu_broadcaster/imu", "imu/data"),
            ("imu_broadcaster/transition_event",
             "_imu_broadcaster/transition_event"),
            (
                "joint_state_broadcaster/transition_event",
                "_joint_state_broadcaster/transition_event",
            ),
            ("~/robot_description", "robot_description"),
        ],
        output="screen",
        condition=UnlessCondition(use_sim_time),
    )

    # 4. Controller Spawner — Referenz-Pattern: einzelner Aufruf mit allen Controllern
    # ALT: 3 separate spawner mit TimerAction(2s/3s/4s) — mögliche Race Condition
    # ALT: joint_state_broadcaster_spawner = Node(...)
    # ALT: mecanum_drive_controller_spawner = Node(...)
    # ALT: imu_broadcaster_spawner = Node(...)
    controllers_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "mecanum_drive_controller",
            "imu_broadcaster",
            "joint_state_broadcaster",
            "-c", "controller_manager",
            "--controller-manager-timeout", "60",
        ],
    )

    # TimerAction: controller_manager muss bereit sein (wie Referenz: 2.0s)
    # ALT: periode war unterschiedlich pro Spawner (2s, 3s, 4s)
    delayed_controllers_spawner = TimerAction(
        period=2.0, actions=[controllers_spawner])

    # Stderr-Monitor: Shutdown bei fatalen Fehlern (Referenz-Pattern)
    # ALT: keine Fehlerüberwachung — Fehler beim Spawnen wurden ignoriert
    def check_if_log_is_fatal(event):
        red_color = "\033[91m"
        reset_color = "\033[0m"
        msg = event.text.decode().lower()
        if (
            "fatal" in msg or "failed" in msg
        ) and "attempt" not in msg:
            print(
                f"{red_color}Fatal error: {event.text}. Emitting shutdown...{reset_color}")
            return EmitEvent(event=Shutdown(reason="Spawner failed"))

    controllers_monitor = RegisterEventHandler(
        OnProcessIO(
            target_action=controllers_spawner,
            on_stderr=check_if_log_is_fatal,
        )
    )

    # 5. Nerf-Kette (nur wenn use_nerf_hardware=true)
    # Spawner startet sequenziell NACH dem Basis-Spawner (OnProcessExit) —
    # verhindert DDS "Thundering Herd" (Pattern aus launch_robot.launch.py).
    nerf_controllers_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "tilt_controller",
            "shooter_controller",
            "arming_controller",
            "-c", "controller_manager",
            "--controller-manager-timeout", "60",
        ],
        output="screen",
        condition=IfCondition(use_nerf_hardware),
    )

    delayed_nerf_spawner = RegisterEventHandler(
        OnProcessExit(
            target_action=controllers_spawner,
            on_exit=[nerf_controllers_spawner],
        )
    )

    nerf_monitor = RegisterEventHandler(
        OnProcessIO(
            target_action=nerf_controllers_spawner,
            on_stderr=check_if_log_is_fatal,
        )
    )

    # High-Level Nerf Control Node — startet nach den Nerf-Spawnern
    nerf_control = Node(
        package="nerf_launch_system",
        executable="nerf_control_node",
        output="screen",
        parameters=[{"auto_arm": auto_arm}],
        remappings=[
            ("/trigger_controller/commands", "/tilt_controller/commands"),
            ("/pusher_controller/commands", "/shooter_controller/commands"),
        ],
        condition=IfCondition(use_nerf_hardware),
    )

    delayed_nerf_control = RegisterEventHandler(
        OnProcessExit(
            target_action=nerf_controllers_spawner,
            on_exit=[nerf_control],
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("use_ros2_control", default_value="true"),
        DeclareLaunchArgument("use_nerf_hardware", default_value="true"),
        DeclareLaunchArgument(
            "use_camera",
            default_value="true",
            description="Include the Gazebo camera sensor in the URDF.",
        ),
        DeclareLaunchArgument(
            "auto_arm",
            default_value="false",
            description="Auto-arm the Nerf launcher on startup",
        ),
        load_urdf,
        twist_mux,
        controller_manager,
        delayed_controllers_spawner,
        controllers_monitor,
        delayed_nerf_spawner,
        nerf_monitor,
        delayed_nerf_control,
    ])
