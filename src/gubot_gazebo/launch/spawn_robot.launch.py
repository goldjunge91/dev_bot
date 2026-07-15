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
Spawn Robot Launch.

==================
Spawnt den Roboter in Gazebo und startet Controller, EKF und per-Robot-Bridge.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_gazebo/launch/spawn_robot.launch.py

Änderungen:
- Pose-Argumente (x, y, z, roll, pitch, yaw) hinzugefügt (Referenz-Pattern)
- -allow_renaming true hinzugefügt (Referenz-Pattern)
- Per-Robot gz_bridge (gubot_bridge.yaml) für Sensor-Topics (Referenz-Pattern)
- SetParameter / SetRemap für korrekte Namespace-Propagation
- LogInfo Welcome-Message (Referenz-Pattern)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = "gubot_gazebo"

    # Pose-Argumente (wie Referenz spawn_robot.launch.py)
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    roll = LaunchConfiguration("roll")
    pitch = LaunchConfiguration("pitch")
    yaw = LaunchConfiguration("yaw")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    use_nerf_hardware = LaunchConfiguration("use_nerf_hardware", default="false")
    use_camera = LaunchConfiguration("use_camera", default="true")

    declare_x_arg = DeclareLaunchArgument(
        "x", default_value="0.0",
        description="Initial robot position in the global 'x' axis.",
    )
    declare_y_arg = DeclareLaunchArgument(
        "y", default_value="0.0",
        description="Initial robot position in the global 'y' axis.",
    )
    declare_z_arg = DeclareLaunchArgument(
        "z", default_value="0.05",
        description="Initial robot position in the global 'z' axis.",
    )
    declare_roll_arg = DeclareLaunchArgument(
        "roll", default_value="0.0",
        description="Initial robot 'roll' orientation.",
    )
    declare_pitch_arg = DeclareLaunchArgument(
        "pitch", default_value="0.0",
        description="Initial robot 'pitch' orientation.",
    )
    declare_yaw_arg = DeclareLaunchArgument(
        "yaw", default_value="0.0",
        description="Initial robot 'yaw' orientation.",
    )

    welcome_msg = LogInfo(
        msg=[
            "Spawning gubot_one\n\tInitial pose: (",
            x, ", ", y, ", ", z, ", ", roll, ", ", pitch, ", ", yaw, ")",
        ]
    )

    # 1. Spawn Robot Entity
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "gubot_one",
            "-allow_renaming", "true",  # NEU: verhindert Konflikte bei Mehrfach-Spawn
            "-topic", "robot_description",
            "-x", x,
            "-y", y,
            "-z", z,
            "-R", roll,
            "-P", pitch,
            "-Y", yaw,
        ],
        output="screen",
    )

    # 2. Per-Robot Sensor Bridge (Referenz: rosbot_bridge.yaml per Robot in spawn_robot)
    gz_robot_bridge_config = PathJoinSubstitution([
        FindPackageShare(package_name), "config", "gubot_bridge.yaml"
    ])
    gz_robot_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gubot_gz_bridge",
        parameters=[{"config_file": gz_robot_bridge_config}],
    )

    # 3. Controller Launch (RSP + Spawners + Twist Mux)
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("gubot_controller"), "launch", "controller.launch.py"
            ])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "use_nerf_hardware": use_nerf_hardware,
            "use_camera": use_camera,
        }.items(),
    )

    # 4. EKF Localization
    ekf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("gubot_localization"), "launch", "ekf.launch.py"
            ])
        ),
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("use_nerf_hardware", default_value="false"),
        DeclareLaunchArgument(
            "use_camera",
            default_value="true",
            description="Include the Gazebo camera sensor in the URDF.",
        ),
        declare_x_arg,
        declare_y_arg,
        declare_z_arg,
        declare_roll_arg,
        declare_pitch_arg,
        declare_yaw_arg,
        # HINWEIS: SetParameter und SetRemap werden NICHT hier gesetzt.
        # Sie wurden bereits global in simulation.launch.py angewendet
        # und propagieren automatisch. Doppelte Setzung fuehrt zu doppelten
        # --ros-args auf rviz2 und anderen Nodes in simulation.launch.py.
        welcome_msg,
        gz_spawn_entity,
        gz_robot_bridge,
        controller_launch,
        ekf_launch,
    ])
