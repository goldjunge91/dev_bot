"""
Controller Launch
=================
Startet robot_state_publisher, twist_mux und alle ros2_control Spawner.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_controller/launch/controller.launch.py

Änderungen:
- Einzelner Spawner für alle 3 Controller mit --controller-manager-timeout 20
  ALT: 3 separate Spawner mit gestaffelten TimerActions (2s/3s/4s) — Race Condition möglich
- OnProcessIO stderr-Monitor für fatale Fehler (Shutdown bei "failed"/"fatal")
  ALT: Keine Fehlerüberwachung
- use_sim_time wird über globalen SetParameter gesetzt (nicht per Node-Parameter)
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessIO
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = "gubot_one"

    use_sim_time = LaunchConfiguration("use_sim_time", default="false")
    use_ros2_control = LaunchConfiguration("use_ros2_control", default="true")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware", default="true")

    # 1. Load URDF (Robot State Publisher)
    # controller_config wird mit Standardpfad geladen (überschreibbar)
    load_urdf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare(package_name), "description", "launch", "load_urdf.launch.py"
            ])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_ros2_control": use_ros2_control,
            "use_nerf_hardware": use_nerf_hardware,
        }.items(),
    )

    # 2. Twist Mux
    twist_mux_config = PathJoinSubstitution([
        FindPackageShare(package_name), "controller", "config", "twist_mux.yaml"
    ])
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_config],
        remappings=[("/cmd_vel_out", "/cmd_vel")],
    )

    # 3. Controller Spawner — Referenz-Pattern: einzelner Aufruf mit allen Controllern
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
            "--controller-manager-timeout", "20",
        ],
    )

    # TimerAction: controller_manager muss bereit sein (wie Referenz: 2.0s)
    # ALT: periode war unterschiedlich pro Spawner (2s, 3s, 4s)
    delayed_controllers_spawner = TimerAction(period=2.0, actions=[controllers_spawner])

    # Stderr-Monitor: Shutdown bei fatalen Fehlern (Referenz-Pattern)
    # ALT: keine Fehlerüberwachung — Fehler beim Spawnen wurden ignoriert
    def check_if_log_is_fatal(event):
        red_color = "\033[91m"
        reset_color = "\033[0m"
        msg = event.text.decode().lower()
        if (
            "fatal" in msg or "failed" in msg
        ) and "attempt" not in msg:
            print(f"{red_color}Fatal error: {event.text}. Emitting shutdown...{reset_color}")
            return EmitEvent(event=Shutdown(reason="Spawner failed"))

    controllers_monitor = RegisterEventHandler(
        OnProcessIO(
            target_action=controllers_spawner,
            on_stderr=check_if_log_is_fatal,
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("use_ros2_control", default_value="true"),
        DeclareLaunchArgument("use_nerf_hardware", default_value="true"),
        load_urdf,
        twist_mux,
        delayed_controllers_spawner,
        controllers_monitor,
    ])
