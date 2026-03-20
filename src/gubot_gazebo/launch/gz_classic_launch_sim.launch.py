import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    pkg_gazebo  = "gubot_gazebo"
    pkg_bringup = "gubot_one_bringup"

    # ── Launch-Argumente ──────────────────────────────────────────────────────
    use_rviz = LaunchConfiguration("use_rviz")
    use_nerf = LaunchConfiguration("use_nerf_hardware")
    gui      = LaunchConfiguration("gui")

    # Als Variable definiert, damit RegisterEventHandler darauf verweisen kann
    spawn_entity = Node(
        package="gazebo_ros", executable="spawn_entity.py",
        arguments=["-topic", "robot_description",
                   "-entity", "gubot_one", "-z", "0.1"],
        output="screen",
    )

    return LaunchDescription([
        # Standard-Konfiguration: gui + rviz + nerf sind immer aktiv.
        # Deaktivierung nur explizit per Argument möglich (z.B. CI/headless).
        DeclareLaunchArgument("use_rviz",          default_value="true",
                              description="RViz2 starten (Standard: true)"),
        DeclareLaunchArgument("use_nerf_hardware", default_value="true",
                              description="NERF-Controller aktivieren (Standard: true)"),
        DeclareLaunchArgument("gui",               default_value="true",
                              description="Gazebo GUI anzeigen (Standard: true)"),

        # ── Robot State Publisher (Classic URDF) ──────────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory(pkg_bringup),
                "launch", "rsp_classic.launch.py")),
            launch_arguments={
                "use_sim_time":    "true",
                "integrated_mode": "true",
                "use_nerf_hardware": use_nerf,
            }.items(),
        ),

        # ── Twist-Mux ─────────────────────────────────────────────────────────
        Node(
            package="twist_mux", executable="twist_mux",
            parameters=[
                os.path.join(get_package_share_directory(pkg_bringup),
                             "config", "twist_mux.yaml"),
                {"use_sim_time": True},
            ],
            remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
        ),

        # ── Gazebo Classic ────────────────────────────────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch", "gazebo.launch.py")),
            launch_arguments={
                "world": os.path.join(
                    get_package_share_directory(pkg_gazebo),
                    "worlds", "obstacles_classic.world"),
                "gui": gui,
                "extra_gazebo_args": "--ros-args --params-file " + os.path.join(
                    get_package_share_directory(pkg_gazebo),
                    "config", "gazebo_params.yaml"),
            }.items(),
        ),

        # ── Roboter spawnen ───────────────────────────────────────────────────
        spawn_entity,

        # ── Controller (erst nach erfolgreichem Spawn) ────────────────────────
        RegisterEventHandler(OnProcessExit(target_action=spawn_entity, on_exit=[
            Node(package="controller_manager", executable="spawner",
                 arguments=["diff_cont"]),
            Node(package="controller_manager", executable="spawner",
                 arguments=["joint_broad"]),
        ])),

        RegisterEventHandler(OnProcessExit(target_action=spawn_entity, on_exit=[
            Node(package="controller_manager", executable="spawner",
                 arguments=["tilt_controller"],
                 condition=IfCondition(use_nerf)),
            Node(package="controller_manager", executable="spawner",
                 arguments=["shooter_controller"],
                 condition=IfCondition(use_nerf)),
            Node(package="controller_manager", executable="spawner",
                 arguments=["arming_controller"],
                 condition=IfCondition(use_nerf)),
        ])),

        # ── RViz (optional) ───────────────────────────────────────────────────
        Node(
            package="rviz2", executable="rviz2",
            arguments=["-d", os.path.join(
                get_package_share_directory(pkg_bringup),
                "config", "view_bot.rviz")],
            condition=IfCondition(use_rviz),
            output="screen",
        ),
    ])
