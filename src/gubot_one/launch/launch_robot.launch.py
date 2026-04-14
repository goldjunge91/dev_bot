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
         * tilt_controller: Tilt Servo
         * shooter_controller: Dart Pusher (FSM/Firmware steuert Flywheels separat)
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
    drive_type = LaunchConfiguration("drive_type")

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
            "drive_type": drive_type,
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
        # ALT: remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
        remappings=[("/cmd_vel_out", "/mecanum_cont/reference_unstamped")],
    )

    # Robot Description für Controller Manager
    pkg_path = os.path.join(get_package_share_directory(package_name))
    xacro_file = os.path.join(pkg_path, "description", "gubot_one_main.urdf.xacro")
    robot_description = Command(
        [
            "xacro ",
            xacro_file,
            " use_ros2_control:=true",
            " sim_mode:=false",
            " integrated_mode:=true",
            " use_nerf_hardware:=",
            use_nerf_hardware,
            " drive_type:=",
            drive_type,
        ]
    )

    # Controller Parameter
    # ALT: controller_params_file = os.path.join(
    # ALT:     get_package_share_directory(package_name), "config", "my_controllers.yaml"
    # ALT: )
    controller_params_file = os.path.join(
        get_package_share_directory(package_name), "config", "mecanum_my_controllers.yaml"
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
    # Kette: diff_cont -> joint_broad -> tilt -> shooter -> arming -> control_node
    # Verwendet OnProcessExit weil Spawner nach erfolgreichem Laden beenden

    from launch.event_handlers import OnProcessExit

    # 1. Controller Spawner (startet nach controller_manager)
    # ALT: diff_drive_spawner = Node(
    # ALT:     package="controller_manager",
    # ALT:     executable="spawner",
    # ALT:     arguments=["diff_cont"],  # Differential Drive Controller
    # ALT: )
    mecanum_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["mecanum_cont"],  # Mecanum Drive Controller
    )

    # ALT: delayed_diff_drive_spawner = RegisterEventHandler(
    # ALT:     event_handler=OnProcessStart(
    # ALT:         target_action=controller_manager,
    # ALT:         on_start=[diff_drive_spawner],
    # ALT:     )
    # ALT: )
    delayed_mecanum_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[mecanum_drive_spawner],
        )
    )

    # 2. Joint Broadcaster (startet nach mecanum_drive_spawner)
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],  # Joint State Broadcaster
    )

    # ALT: delayed_joint_broad_spawner = RegisterEventHandler(
    # ALT:     event_handler=OnProcessExit(
    # ALT:         target_action=diff_drive_spawner,
    # ALT:         on_exit=[joint_broad_spawner],
    # ALT:     )
    # ALT: )
    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=mecanum_drive_spawner,
            on_exit=[joint_broad_spawner],
        )
    )

    # 3. Nerf Tilt Controller (startet nach joint_broad)
    nerf_tilt_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller"],  # Tilt Servo
        output="screen",
    )

    delayed_nerf_tilt = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_broad_spawner,
            on_exit=[nerf_tilt_spawner],
        )
    )

    # 4. Nerf Shooter Controller (startet nach tilt)
    nerf_shooter_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],  # Dart Pusher/FSM-Eingang
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
        remappings=[
            ("/trigger_controller/commands", "/tilt_controller/commands"),
            ("/pusher_controller/commands", "/shooter_controller/commands"),
        ],
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
            DeclareLaunchArgument(
                "drive_type",
                default_value="mecanum",
                description="Type of drive system (diffdrive, mecanum)",
            ),
            rsp,
            joystick,
            twist_mux,
            delayed_controller_manager,
            # ALT: delayed_diff_drive_spawner,
            delayed_mecanum_drive_spawner,
            delayed_joint_broad_spawner,
            nerf_group,
        ]
    )
