"""
Robot State Publisher (RSP) Launch
===================================
Publiziert die Roboter-Beschreibung (URDF) und TF-Transformationen.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_description/launch/load_urdf.launch.py

Änderungen gegenüber vorheriger Version:
- controller_config Argument hinzugefügt (Pfad wird in xacro injiziert)
  ALT: Pfad war im xacro hard-coded
- SetParameter(use_sim_time) und SetRemap(/tf, /tf_static) wie Referenz
- PathJoinSubstitution / FindPackageShare statt os.path.join / get_package_share_directory

Launch Arguments:
- use_sim_time: false (Standard) - Nutzt echte Hardware-Zeit
- use_ros2_control: true (Standard) - Aktiviert ros2_control
- use_nerf_hardware: true (Standard) - Nerf Hardware aktivieren
# ALT: - use_gazebo_classic: false (Standard) - Ignition Fortress verwenden
- controller_config: Pfad zu controllers.yaml (Standard: gubot_one Paket)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch Configuration Variablen
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_ros2_control = LaunchConfiguration("use_ros2_control")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    use_camera = LaunchConfiguration("use_camera")
    # ALT: use_gazebo_classic = LaunchConfiguration("use_gazebo_classic")
    controller_config = LaunchConfiguration("controller_config")

    # Xacro-Datei und Parameter
    # Command() führt xacro zur Laufzeit aus und injiziert alle Argumente
    xacro_file = PathJoinSubstitution([
        FindPackageShare("gubot_one"), "description", "urdf", "gubot_one_main.urdf.xacro"
    ])

    # ALT: os.path.join(get_package_share_directory("gubot_one"), ...)
    # Ersetzt durch PathJoinSubstitution
    robot_description_config = Command([
        "xacro ",
        xacro_file,
        " use_ros2_control:=", use_ros2_control,
        " sim_mode:=", use_sim_time,
        " use_nerf_hardware:=", use_nerf_hardware,
        " use_camera:=", use_camera,
        # ALT: " use_gazebo_classic:=", use_gazebo_classic,
        " use_gazebo_classic:=false",
        # NEU: controller_config wird in xacro injiziert (ALT: hard-coded im xacro)
        " controller_config:=", controller_config,
    ])

    params = {
        "robot_description": ParameterValue(robot_description_config, value_type=str),
    }

    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[params],
    )

    return LaunchDescription([
        # Launch Arguments (Referenz-Reihenfolge: Args zuerst, dann Actions)
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use sim time if true",
        ),
        DeclareLaunchArgument(
            "use_ros2_control",
            default_value="true",
            description="Use ros2_control if true",
        ),
        DeclareLaunchArgument(
            "use_nerf_hardware",
            default_value="true",
            description="Enable Nerf hardware if true",
        ),
        DeclareLaunchArgument(
            "use_camera",
            default_value="true",
            description="Include the Gazebo camera sensor in the URDF "
                        "(false: no render sensor, camera TF frames stay).",
        ),
        # DeclareLaunchArgument(
        #     "use_gazebo_classic",
        #     default_value="false",
        #     description="Use Gazebo Classic if true (default: Ignition Fortress)",
        # ),
        # NEU: controller_config Argument — Pfad zu controllers.yaml (Referenz-Pattern)
        # ALT: Pfad war im xacro ros2_control_gazebo_ign_fortress.xacro hard-coded
        DeclareLaunchArgument(
            "controller_config",
            default_value=PathJoinSubstitution([
                FindPackageShare("gubot_one"), "controller", "config", "controllers.yaml"
            ]),
            description="Absolute path to controllers.yaml, injected into URDF xacro.",
        ),
        # HINWEIS: SetParameter(use_sim_time) und SetRemap werden NICHT hier gesetzt.
        # Sie werden global in simulation.launch.py gesetzt und propagieren
        # durch spawn_robot -> controller.
        # ALT: SetParameter / SetRemap hier -> gedoppelte Remaps auf Spawner-Cmd.
        node_robot_state_publisher,
    ])
