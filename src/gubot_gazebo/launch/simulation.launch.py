import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    AppendEnvironmentVariable,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    package_name = "gubot_gazebo"

    # Declare the 'world' argument
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=os.path.join(
            get_package_share_directory(package_name), "worlds", "obstacles.world"
        ),
        description="World to load",
    )

    # Gazebo Sim (Ignition)
    # gazebo = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         [
    #             os.path.join(
    #                 get_package_share_directory("ros_gz_sim"),
    #                 "launch",
    #                 "gz_sim.launch.py",
    #             )
    #         ]
    #     ),
    #     launch_arguments={
    #         "gz_args": [LaunchConfiguration("world"), " -r -v 4 --render-engine-server ogre --render-engine-gui ogre"]
    #     }.items(),
    # )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                )
            ]
        ),
        launch_arguments={
            "gz_args": [
                "-r -v4 --render-engine-server ogre --render-engine-gui ogre ",
                LaunchConfiguration("world"),
            ],
            "on_exit_shutdown": "true",
        }.items(),
    )
    # Global GZ Bridge (Clock)
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": os.path.join(
                    get_package_share_directory(package_name),
                    "config",
                    "gz_bridge.yaml",
                )
            }
        ],
        output="screen",
    )

    # Spawn Robot
    spawn_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "spawn_robot.launch.py",
                )
            ]
        ),
        launch_arguments={"use_rviz": "true"}.items(),
    )

    return LaunchDescription(
        [
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.path.expanduser("~"), ".ignition", "gazebo", "models"),
            ),
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
            ),
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.getcwd(), "src"),
            ),
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.getcwd(), "install", "nerf_launch_system", "share"),
            ),
            AppendEnvironmentVariable(
                "IGN_GAZEBO_RESOURCE_PATH",
                os.path.join(os.getcwd(), "install", "gubot_one_description", "share"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.path.expanduser("~"), ".ignition", "gazebo", "models"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.getcwd(), "src"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.getcwd(), "install", "nerf_launch_system", "share"),
            ),
            AppendEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                os.path.join(os.getcwd(), "install", "gubot_one_description", "share"),
            ),
            # Native WSLg Hardware Acceleration (D3D12 / Intel UHD)
            # SetEnvironmentVariable("DISPLAY", ":0"),
            # SetEnvironmentVariable("WAYLAND_DISPLAY", "wayland-0"),
            # SetEnvironmentVariable("LIBGL_ALWAYS_INDIRECT", "0"),
            # SetEnvironmentVariable("LIBGL_ALWAYS_SOFTWARE", "0"),
            # SetEnvironmentVariable("GALLIUM_DRIVER", "d3d12"),
            # SetEnvironmentVariable("MESA_D3D12_DEFAULT_ADAPTER_NAME", "NVIDIA"),
            # SetEnvironmentVariable("LIBGL_DRI3_DISABLE", "1"),
            # AppendEnvironmentVariable("LD_LIBRARY_PATH", "/usr/lib/wsl/lib"),
            # # DDS / Middleware fixes for WSL2 (Force local communication)
            # SetEnvironmentVariable("ROS_LOCALHOST_ONLY", "1"),
            SetEnvironmentVariable("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp"),
            # SetEnvironmentVariable("MESA_GL_VERSION_OVERRIDE", "4.1"),
            # SetEnvironmentVariable("MESA_GLSL_VERSION_OVERRIDE", "410"),
            SetEnvironmentVariable("MESA_SHADER_CACHE_DISABLE", "true"),
            # SetEnvironmentVariable("IGN_GAZEBO_RENDER_ENGINE_NAME", "ogre2"),
            SetEnvironmentVariable("GZ_IP", "127.0.0.1"),
            SetEnvironmentVariable("IGN_IP", "127.0.0.1"),
            SetEnvironmentVariable("GZ_TRANSPORT_RCVHWM", "1000"),
            world_arg,
            gazebo,
            gz_bridge,
            spawn_robot,
        ]
    )
