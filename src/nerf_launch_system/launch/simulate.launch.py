# Copyright 2026 Developer
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

# Simulation Launch File fuer Nerf Standalone System
# Startet Gazebo-Simulation mit ROS2 Control und RViz
#
# World-Dateien zentral in gubot_gazebo/worlds/ (Phase 2 Refactoring):
#   Ignition default : empty_ignition_standalone.world
#   Classic default  : obstacles_classic.world
#
# Launch-File Struktur:
# 1. Imports
# 2. LaunchConfiguration
# 3. DeclareLaunchArgument
# 4. Nodes
# 5. LaunchDescription

from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    package_name = "nerf_launch_system"

    pkg_nerf = get_package_share_directory("nerf_launch_system")
    pkg_gazebo_ros = get_package_share_directory("gazebo_ros")

    # Worlds zentral aus gubot_gazebo (Phase 2)
    # VORHER: os.path.join(pkg_nerf, "worlds", "empty.world")
    pkg_gubot_gazebo = get_package_share_directory("gubot_gazebo")
    default_world = os.path.join(
        pkg_gubot_gazebo, "worlds", "empty_ignition_standalone.world"
    )

    world_arg = DeclareLaunchArgument(
        "world",
        default_value=default_world,
        description="World to load. Ignition default: empty_ignition_standalone.world, "
                    "Classic default: obstacles_classic.world (beide in gubot_gazebo/worlds/)",
    )

    use_gazebo_classic_arg = DeclareLaunchArgument(
        "use_gazebo_classic",
        default_value="false",
        description="Whether to use Gazebo Classic (true) or Gazebo Ignition/Harmonic (false)",
    )

    use_gazebo_classic = LaunchConfiguration("use_gazebo_classic")

    def launch_setup(context):
        use_classic = (
            context.launch_configurations.get("use_gazebo_classic", "false").lower()
            == "true"
        )
        xacro_file = os.path.join(
            pkg_nerf, "description", "urdf", "launcher.urdf.xacro"
        )
        robot_description_config = xacro.process_file(
            xacro_file,
            mappings={"use_gazebo_classic": "true" if use_classic else "false"},
        )

        node_robot_state_publisher = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[
                {"use_sim_time": True},
                {"robot_description": robot_description_config.toxml()},
            ],
        )
        return [node_robot_state_publisher]

    # Gazebo Classic
    gazebo_params_file = os.path.join(
        get_package_share_directory(package_name), "config", "gazebo_params.yaml"
    )
    gazebo_classic = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world": LaunchConfiguration("world"),
            "extra_gazebo_args": "--verbose --ros-args --params-file "
            + gazebo_params_file,
        }.items(),
        condition=IfCondition(use_gazebo_classic),
    )

    spawn_entity_classic = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "nerf_launcher"],
        output="screen",
        condition=IfCondition(use_gazebo_classic),
    )

    # Modern Gazebo (Ignition/Harmonic)
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")
    gazebo_ign = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": [LaunchConfiguration("world"), " -r -v 4 --render-engine ogre"]
        }.items(),
        condition=UnlessCondition(use_gazebo_classic),
    )

    spawn_entity_ign = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "robot_description",
            "-name", "nerf_launcher",
            "-z", "0.5",
        ],
        output="screen",
        condition=UnlessCondition(use_gazebo_classic),
    )

    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        condition=UnlessCondition(use_gazebo_classic),
    )

    rviz_config = os.path.join(pkg_nerf, "config", "view_v1.rviz")
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    tilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["tilt_controller"],
        output="screen",
    )

    shooter_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["shooter_controller"],
        output="screen",
    )

    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
        output="screen",
    )

    return LaunchDescription([
        use_gazebo_classic_arg,
        world_arg,
        OpaqueFunction(function=launch_setup),
        gazebo_classic,
        spawn_entity_classic,
        gazebo_ign,
        spawn_entity_ign,
        ros_gz_bridge,
        joint_state_broadcaster_spawner,
        tilt_controller_spawner,
        shooter_controller_spawner,
        arming_controller_spawner,
        rviz,
    ])
