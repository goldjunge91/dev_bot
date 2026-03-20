import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    RegisterEventHandler,
    AppendEnvironmentVariable,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():

    package_name = "gubot_one"

    # --- Gleiche Reihenfolge wie articubot_one/launch/launch_sim.launch.py ---

    # 1. Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), "launch", "rsp.launch.py"
        )]),
        launch_arguments={
            "use_sim_time": "true",
            "use_ros2_control": "true",
            "integrated_mode": "true",  # gubot_one: Nerf + Basis als ein System
        }.items(),
    )


    # 2. Joystick
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), "launch", "joystick.launch.py"
        )]),
        launch_arguments={"use_sim_time": "true"}.items(),
    )

    # 3. Twist Mux
    twist_mux_params = os.path.join(
        get_package_share_directory(package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
    )

    # 4. World
    default_world = os.path.join(
        get_package_share_directory(package_name), "worlds", "obstacles.world"
    )
    world = LaunchConfiguration("world")
    world_arg = DeclareLaunchArgument(
        "world",
        default_value=default_world,
        description="World to load",
    )

    # 5. Gazebo (Ignition)
    # on_exit_shutdown: beendet alle Nodes wenn Gazebo geschlossen wird
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
        )]),
        launch_arguments={
            "gz_args": ["-r -v4 ", world],
            "on_exit_shutdown": "true",
        }.items(),
    )


    # 6. Spawn Entity
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "gubot_one", "-z", "0.1"],
        output="screen",
    )

    # 7. diff_drive_spawner (wie articubot_one, condition ist gubot_one-Zusatz)
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )

    # 8. joint_broad_spawner
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )

    # 9. ROS <-> GZ Bridge (parameter_bridge fuer alle non-image Topics)
    bridge_params = os.path.join(
        get_package_share_directory(package_name), "config", "gz_bridge.yaml"
    )
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["--ros-args", "-p", f"config_file:={bridge_params}"],
        output="screen",
    )

    # 10. Image Bridge (separater Node fuer /camera/image_raw – zuverlaessiger als parameter_bridge)
    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"],
        output="screen",
    )


    # --- gubot_one Zusaetze (alles was articubot_one nicht hat) ---

    # 11. IMU Broadcaster
    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["imu_broadcaster"],
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )

    # 12. Nerf Launcher Controller
    flywheel_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["flywheel_controller"],
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )
    trigger_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["trigger_controller"],
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )
    pusher_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pusher_controller"],
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )
    arming_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arming_controller"],
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_ros2_controllers")),
    )


    # 13. Event Handler – alle Spawner warten auf spawn_entity
    # condition= sitzt auf dem Node (siehe oben), NICHT auf RegisterEventHandler
    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[diff_drive_spawner])
    )
    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[joint_broad_spawner])
    )
    delayed_imu_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[imu_broadcaster_spawner])
    )
    delayed_nerf_flywheel = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[flywheel_controller_spawner])
    )
    delayed_nerf_trigger = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[trigger_controller_spawner])
    )
    delayed_nerf_pusher = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[pusher_controller_spawner])
    )
    delayed_nerf_arming = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[arming_controller_spawner])
    )

    # 14. RViz
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(
            get_package_share_directory(package_name), "config", "view_bot.rviz"
        )],
        output="screen",
    )


    # --- Launch them all! (Reihenfolge wie articubot_one, gubot_one-Extras am Ende) ---
    return LaunchDescription([

        # gubot_one: Umgebungsvariablen
        # FIX: SetEnvironmentVariable (nicht Append) – ueberschreibt einen bereits
        # in der Shell gesetzten CYCLONEDDS_URI. Append wuerde zwei Pfade mit ':'
        # verketten → CycloneDDS-Domain-Init schlaegt fehl → alle Nodes crashen.
        # Fuer Simulation: leerer String → CycloneDDS nutzt Standard (loopback),
        # nicht das Tailscale-Interface aus pc_cyclonedds.xml.
        SetEnvironmentVariable("CYCLONEDDS_URI", ""),
        AppendEnvironmentVariable(
            "IGN_GAZEBO_RESOURCE_PATH",
            os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
        ),
        AppendEnvironmentVariable(
            "GAZEBO_MODEL_PATH",
            os.path.join(os.path.expanduser("~"), ".gazebo", "models"),
        ),
        AppendEnvironmentVariable("MESA_GL_VERSION_OVERRIDE", "4.5"),
        AppendEnvironmentVariable("MESA_GLSL_VERSION_OVERRIDE", "450"),
        AppendEnvironmentVariable("GZ_TRANSPORT_RCVHWM", "1000"),

        # gubot_one: Launch Arguments
        DeclareLaunchArgument("use_sim_time", default_value="true",
                              description="Use sim time if true"),
        DeclareLaunchArgument("enable_ros2_controllers", default_value="true",
                              description="Spawn ros2_control controllers after entity spawn"),

        # articubot_one Reihenfolge
        rsp,
        joystick,
        twist_mux,
        world_arg,
        gazebo,
        spawn_entity,
        ros_gz_bridge,
        ros_gz_image_bridge,

        # gubot_one Zusaetze
        rviz_node,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner,
        delayed_imu_broadcaster_spawner,
        delayed_nerf_flywheel,
        delayed_nerf_trigger,
        delayed_nerf_pusher,
        delayed_nerf_arming,
    ])
