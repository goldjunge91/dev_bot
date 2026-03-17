"""
Launch Robot - Roboter-Basis mit ros2_control
==============================================
Startet die Hauptkomponenten des Roboters

Komponenten:
1. Robot State Publisher (rsp.launch.py)
   - Publiziert URDF/TF-Transformationen

2. Joystick (joystick.launch.py)
   - Controller-Eingabe (joy_node läuft extern)

3. Twist Mux
   - Multiplexer für verschiedene Geschwindigkeitsquellen
   - Priorität: Joystick > Tracker > Keyboard

4. Controller Manager (ros2_control_node)
   - Verwaltet alle Hardware-Controller
   - Startet nach 3 Sekunden Verzögerung

5. Controller Spawner (sequenziell gestartet)
   - diff_cont: Differential Drive Controller
   - joint_broad: Joint State Broadcaster
   - Nerf Controller (nur wenn use_nerf_hardware=true):
     * trigger_controller: Tilt Servo
     * flywheel_controller: Flywheel Motoren
     * pusher_controller: Dart Pusher
     * arming_controller: Sicherheitssystem
   - nerf_control_node: High-Level Nerf Control

WICHTIG: Sequenzielles Starten verhindert DDS "Thundering Herd"
Jeder Controller wartet bis der vorherige erfolgreich geladen ist.

Launch Arguments:
- use_nerf_hardware: false (Standard)

Verwendung:
  ros2 launch gubot_one_bringup launch_robot.launch.py
  ros2 launch gubot_one_bringup launch_robot.launch.py use_nerf_hardware:=true
"""

import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
    DeclareLaunchArgument,
    GroupAction,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch.event_handlers import OnProcessStart, OnProcessExit
from launch.conditions import IfCondition

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_one_bringup"

    # Launch Configuration
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    use_sim_time = LaunchConfiguration("use_sim_time")
    auto_arm = LaunchConfiguration("auto_arm")

    # 1. Robot State Publisher
    # Publiziert URDF und TF-Transformationen
    # rsp = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         [
    #             os.path.join(
    #                 get_package_share_directory(package_name), "launch", "rsp.launch.py"
    #             )
    #         ]
    #     ),
    #     launch_arguments={
    #         "use_sim_time": "false",  # Echte Hardware, keine Simulation
    #         "use_ros2_control": "true",  # ros2_control aktivieren
    #         "integrated_mode": "true",  # Integrierter Modus (Nerf + Basis zusammen)
    #         "use_nerf_hardware": use_nerf_hardware,
    #     }.items(),
    # )
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
            "use_nerf_hardware": use_nerf_hardware,
            "use_fake_hardware": use_fake_hardware,
        }.items(),
    )

    # 2. Joystick
    # Controller-Eingabe (joy_node läuft extern auf anderem Gerät)
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

    # 3. Twist Mux
    # Multiplexer für verschiedene Geschwindigkeitsquellen
    # Priorität: Joystick > Tracker > Keyboard
    twist_mux_params = os.path.join(
        get_package_share_directory(package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
    )

    # Robot Description für Controller Manager
    pkg_path = os.path.join(get_package_share_directory("gubot_one_description"))
    xacro_file = os.path.join(pkg_path, "description", "robot.urdf.xacro")
    # robot_description = Command(
    #     [
    #         "xacro ",
    #         xacro_file,
    #         " use_ros2_control:=true",
    #         " sim_mode:=false",
    #         " integrated_mode:=true",
    #         " use_nerf_hardware:=",
    #         use_nerf_hardware,
    #     ]
    # )
    robot_description = Command(
        [
            "xacro ",
            xacro_file,
            " use_ros2_control:=true",
            " sim_mode:=",
            use_sim_time,
            " integrated_mode:=true",
            " use_nerf_hardware:=",
            use_nerf_hardware,
            " use_fake_hardware:=",
            use_fake_hardware,
        ]
    )

    # Controller Parameter
    controller_params_file = os.path.join(
        get_package_share_directory(package_name), "config", "my_controllers.yaml"
    )

    # 4. Controller Manager
    # Verwaltet alle Hardware-Controller
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[{"robot_description": robot_description}, controller_params_file],
    )

    # Verzögere Controller Manager Start um 3 Sekunden
    # Gibt anderen Nodes Zeit zum Starten (nur bei echter Hardware nötig)
    # delayed_controller_manager = TimerAction(period=3.0, actions=[controller_manager])

    # NEW: Delay only for real hardware

    def launch_setup(context, *args, **kwargs):
        use_fake = (
            context.launch_configurations.get("use_fake_hardware", "false").lower()
            == "true"
        )
        if use_fake:
            return [controller_manager]
        else:
            return [TimerAction(period=3.0, actions=[controller_manager])]

    delayed_controller_manager_action = OpaqueFunction(function=launch_setup)

    # --- Controller Spawner Sequenz ---
    # Verhindert "Thundering Herd" auf DDS durch sequenzielles Starten
    # Kette: diff_cont -> joint_broad -> trigger -> flywheel -> pusher -> arming -> control_node
    # Verwendet OnProcessExit weil Spawner nach erfolgreichem Laden beenden

    # 1. Diff Drive Controller (startet nach controller_manager)
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],  # Differential Drive Controller
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner],
        )
    )

    # 2. Joint Broadcaster (startet nach diff_drive)
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],  # Joint State Broadcaster
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=diff_drive_spawner,
            on_exit=[joint_broad_spawner],
        )
    )

    # Node: Spawner für imu_broadcaster
    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster"],
    )

    # 3. Nerf Tilt Controller (startet nach imu_broadcaster)
    nerf_tilt_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller"],  # Tilt Servo
        output="screen",
    )

    delayed_imu_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_broad_spawner,
            on_exit=[imu_broadcaster_spawner],
        )
    )

    delayed_nerf_tilt = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=imu_broadcaster_spawner,
            on_exit=[nerf_tilt_spawner],
        )
    )

    # 4. Nerf Shooter Controller (startet nach tilt)
    nerf_shooter_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],  # Shooter
        output="screen",
    )

    delayed_nerf_shooter = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_tilt_spawner,
            on_exit=[nerf_shooter_spawner],
        )
    )

    # 5. Nerf Arming Controller (startet nach shooter)
    nerf_arming_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],  # Sicherheitssystem
        output="screen",
    )

    delayed_nerf_arming = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_shooter_spawner,
            on_exit=[nerf_arming_spawner],
        )
    )

    # 6. Nerf Control Node (startet nach arming)
    nerf_control = Node(
        package="nerf_launch_system",
        executable="nerf_control_node",
        output="screen",
        parameters=[{"auto_arm": auto_arm}],
    )

    delayed_nerf_control = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_arming_spawner,
            on_exit=[nerf_control],
        )
    )

    # Nerf Gruppe: Alle Nerf-Controller zusammengefasst
    # Wird nur gestartet wenn use_nerf_hardware=true
    nerf_group = GroupAction(
        condition=IfCondition(use_nerf_hardware),
        actions=[
            delayed_nerf_tilt,
            delayed_nerf_shooter,
            delayed_nerf_arming,
            delayed_nerf_control,
        ],
    )

    # --- NEW IMU FILTER ---
    imu_filter_node = Node(
        package="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        name="imu_filter",
        output="screen",
        parameters=[
            {
                "use_mag": False,
                "publish_tf": False,
                "world_frame": "enu",
                "fixed_frame": "odom",
                "gain": 0.01,  # Reduziert Drift im Stand (weniger Gyro-Einfluss)
                "zeta": 0.0,  # Gyro-Bias Korrektur
            }
        ],
        remappings=[
            ("/imu/data_raw", "/imu_broadcaster/imu"),
            ("/imu/data", "/imu/data"),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_nerf_hardware",
                default_value="false",
                description="Enable Nerf hardware if true",
            ),
            DeclareLaunchArgument(
                "use_fake_hardware",
                default_value="false",
                description="Enable fake hardware if true",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="Use simulation time if true",
            ),
            DeclareLaunchArgument(
                "auto_arm",
                default_value="false",
                description="Auto-arm the Nerf launcher on startup",
            ),
            rsp,
            joystick,
            twist_mux,
            delayed_controller_manager_action,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner,
            delayed_imu_broadcaster_spawner,
            nerf_group,
            imu_filter_node,
        ]
    )
