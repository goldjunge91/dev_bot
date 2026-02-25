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
  ros2 launch gubot_one launch_robot.launch.py
  ros2 launch gubot_one launch_robot.launch.py use_nerf_hardware:=true
"""

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
    package_name = "gubot_one"

    # Launch Configuration
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    auto_arm = LaunchConfiguration("auto_arm")

    # 1. Robot State Publisher
    # Publiziert URDF und TF-Transformationen
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name), "launch", "rsp.launch.py"
                )
            ]
        ),
        launch_arguments={
            "use_sim_time": "false",  # Echte Hardware, keine Simulation
            "use_ros2_control": "true",  # ros2_control aktivieren
            "integrated_mode": "true",  # Integrierter Modus (Nerf + Basis zusammen)
            "use_nerf_hardware": use_nerf_hardware,
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
    # Gibt anderen Nodes Zeit zum Starten
    delayed_controller_manager = TimerAction(period=3.0, actions=[controller_manager])

    # --- Controller Spawner Sequenz ---
    # Verhindert "Thundering Herd" auf DDS durch sequenzielles Starten
    # Kette: diff_cont -> joint_broad -> trigger -> flywheel -> pusher -> arming -> control_node
    # Verwendet OnProcessExit weil Spawner nach erfolgreichem Laden beenden

    from launch.event_handlers import OnProcessExit

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

    # 3. Nerf Trigger Controller (startet nach joint_broad)
    nerf_trigger_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller"],  # Tilt Servo
        output="screen",
    )

    delayed_nerf_trigger = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_broad_spawner,
            on_exit=[nerf_trigger_spawner],
        )
    )

    # 4. Nerf Flywheel Controller (startet nach trigger)
    nerf_flywheel_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["flywheel_controller"],  # Flywheel Motoren
        output="screen",
    )

    delayed_nerf_flywheel = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_trigger_spawner,
            on_exit=[nerf_flywheel_spawner],
        )
    )

    # 5. Nerf Pusher Controller (startet nach flywheel)
    nerf_pusher_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller"],  # Dart Pusher
        output="screen",
    )

    delayed_nerf_pusher = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_flywheel_spawner,
            on_exit=[nerf_pusher_spawner],
        )
    )

    # 6. Nerf Arming Controller (startet nach pusher)
    nerf_arming_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],  # Sicherheitssystem
        output="screen",
    )

    delayed_nerf_arming = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=nerf_pusher_spawner,
            on_exit=[nerf_arming_spawner],
        )
    )

    # 7. Nerf Control Node (startet nach arming)
    nerf_control = Node(
        package="nerf_standalone",
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
            delayed_nerf_trigger,
            delayed_nerf_flywheel,
            delayed_nerf_pusher,
            delayed_nerf_arming,
            delayed_nerf_control,
        ],
    )

    # Starte alle Komponenten
    # Nur der erste Trigger muss zurückgegeben werden
    # Der Rest startet automatisch über Events
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_nerf_hardware",
                default_value="false",
                description="Enable Nerf hardware if true",
            ),
            DeclareLaunchArgument(
                "auto_arm",
                default_value="false",
                description="Auto-arm the Nerf launcher on startup",
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
