# Copyright 2026 goldjunge91
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simulation Launch.

=================
Startet Gazebo, den globalen Clock-Bridge und spawnt den Roboter.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_gazebo/launch/simulation.launch.py

Änderungen:
- SetEnvironmentVariable, SetRemap, SetParameter global gesetzt (Referenz-Pattern)
- gz_log_level 1 statt -v4 (weniger Ausgabe)
- husarion_gz_worlds NICHT verfügbar — lokale World-Datei wird verwendet
- ros_gz_image_bridge entfernt — Bild-Bridging jetzt in gubot_bridge.yaml (spawn_robot)
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
    package_name = "gubot_gazebo"

    world_arg = DeclareLaunchArgument(
        "world",
        # obstacles.world nutzt construction_cone/barrel — die Modelle sind
        # jetzt in gazebo/models/ vendored und werden über den env-hook
        # (IGN_GAZEBO_RESOURCE_PATH, siehe CMakeLists ament_environment_hooks)
        # gefunden.
        default_value=PathJoinSubstitution([
            FindPackageShare(package_name), "worlds", "obstacles.world"
        ]),
        description="Ignition Gazebo World File (Standard: obstacles.world)",
    )

    use_nerf_hardware_arg = DeclareLaunchArgument(
        "use_nerf_hardware",
        default_value="true",
        description="Enable nerf hardware if true",
    )

    # Kamera-Sensor abschaltbar: unter WSL2 rendert die 640x480-Kamera per
    # Software-GL (llvmpipe) auf der CPU und drueckt den RTF massiv.
    # use_camera:=false entfernt nur den Gazebo-Render-Sensor — Links und
    # TF-Frames der Kamera bleiben erhalten (RViz-Konfig bricht nicht).
    use_camera_arg = DeclareLaunchArgument(
        "use_camera",
        default_value="true",
        description="Include the Gazebo camera sensor "
                    "(false: faster sim on WSL2, camera TF frames stay).",
    )

    declare_rviz_arg = DeclareLaunchArgument(
        "rviz",
        default_value="True",
        description="Run RViz simultaneously.",
        choices=["True", "true", "False", "false"],
    )

    world = LaunchConfiguration("world")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware")
    use_camera = LaunchConfiguration("use_camera")
    rviz = LaunchConfiguration("rviz")

    # Gazebo (Ignition Fortress / gz_sim)
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
    gz_bridge_config = PathJoinSubstitution([
        FindPackageShare(package_name), "config", "gz_bridge.yaml"
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
                FindPackageShare(package_name), "launch", "spawn_robot.launch.py"
            ])
        ),
        launch_arguments={
            "use_nerf_hardware": use_nerf_hardware,
            "use_camera": use_camera,
        }.items(),
    )

    # RViz (Referenz: description/launch/rviz.launch.py — hier direkter Node)
    rviz_config = PathJoinSubstitution([
        FindPackageShare("gubot_description"), "rviz", "main.rviz"
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
        use_camera_arg,
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
