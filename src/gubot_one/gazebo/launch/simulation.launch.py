"""
Simulation Launch
=================
Startet Gazebo, den globalen Clock-Bridge und spawnt den Roboter.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_gazebo/launch/simulation.launch.py

Änderungen:
- SetEnvironmentVariable, SetRemap, SetParameter global gesetzt (Referenz-Pattern)
  ALT: use_sim_time wurde nur per Node-Parameter gesetzt
- gz_log_level 1 statt -v4 (weniger Ausgabe)
  ALT: gz_args="-r -v4 <world>"
- husarion_gz_worlds NICHT verfügbar — lokale World-Datei wird verwendet
  ALT (Referenz): FindPackageShare("husarion_gz_worlds")
- ros_gz_image_bridge entfernt — Bild-Bridging jetzt in gubot_bridge.yaml (spawn_robot)
  ALT: ros_gz_image_bridge Node war hier inline
- gz_bridge.yaml enthält nur /clock (global); Sensor-Topics in gubot_bridge.yaml (per Robot)
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node, SetParameter, SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = "gubot_one"

    world_arg = DeclareLaunchArgument(
        "world",
        # ALT: obstacles.world — verwendet construction_cone/barrel Modelle
        # die nicht installiert sind. Fuer obstacles.world muss
        # IGN_GAZEBO_RESOURCE_PATH auf die Modell-Verzeichnisse zeigen.
        # Beispiel:
        # ros2 launch gubot_one simulation.launch.py \
        #   world:=$(ros2 pkg prefix gubot_one)/share/.../obstacles.world
        default_value=PathJoinSubstitution([
            FindPackageShare(package_name), "gazebo", "worlds", "empty.world"
        ]),
        description="Ignition Gazebo World File (Standard: empty.world)",
    )

    use_nerf_hardware_arg = DeclareLaunchArgument(
        "use_nerf_hardware",
        default_value="true",
        description="Enable nerf hardware if true",
    )

    declare_rviz_arg = DeclareLaunchArgument(
        "rviz",
        default_value="True",
        description="Run RViz simultaneously.",
        choices=["True", "true", "False", "false"],
    )

    world = LaunchConfiguration("world")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    rviz = LaunchConfiguration("rviz")

    # Gazebo (Ignition Fortress / gz_sim)
    # ALT (Referenz): husarion_gz_worlds nicht verfügbar, daher lokale World-Datei
    # ALT: gz_args="-r -v4 <world>" — zu viel Logging-Ausgabe
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("husarion_gz_worlds"), "launch", "gz_sim.launch.py"
            ])
        ),
        launch_arguments={
            "gz_world": world,
            "gz_log_level": "1",
        }.items(),
    )

    # Globaler Clock-Bridge (nur /clock — Sensor-Topics in gubot_bridge.yaml per Robot)
    # ALT: gz_bridge.yaml enthielt auch scan und camera/camera_info (falsche Scope)
    gz_bridge_config = PathJoinSubstitution([
        FindPackageShare(package_name), "gazebo", "config", "gz_bridge.yaml"
    ])
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        parameters=[{"config_file": gz_bridge_config}],
    )

    # Spawn Robot (inkl. controller, EKF, per-robot bridge)
    spawn_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare(package_name), "gazebo", "launch", "spawn_robot.launch.py"
            ])
        ),
        launch_arguments={"use_nerf_hardware": use_nerf_hardware}.items(),
    )

    # RViz (Referenz: description/launch/rviz.launch.py — hier direkter Node)
    rviz_config = PathJoinSubstitution([
        FindPackageShare(package_name), "description", "rviz", "main.rviz"
    ])
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(rviz),
    )

    return LaunchDescription([
        world_arg,
        use_nerf_hardware_arg,
        declare_rviz_arg,
        # NEU: Globale SetEnvironmentVariable, SetRemap, SetParameter (Referenz-Pattern)
        SetEnvironmentVariable(name="RCUTILS_COLORIZED_OUTPUT", value="1"),
        # NEU: Software-Rendering erzwingen (verhindert GL3PlusTextureGpu/OGRE-Absturz unter WSL2)
        SetEnvironmentVariable(name="LIBGL_ALWAYS_SOFTWARE", value="1"),
        SetRemap("/diagnostics", "diagnostics"),
        SetRemap("/tf", "tf"),
        SetRemap("/tf_static", "tf_static"),
        SetParameter(name="use_sim_time", value=True),
        gz_sim,
        gz_bridge,
        spawn_robot,
        rviz_node,
    ])
