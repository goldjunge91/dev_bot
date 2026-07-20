from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    use_mock_hardware_arg = DeclareLaunchArgument(
        "use_mock_hardware",
        default_value="false",
        description="Use mock_components/GenericSystem instead of real Pico hardware.",
    )
    use_rviz_arg = DeclareLaunchArgument(
        "use_rviz", default_value="true", description="Start RViz2."
    )

    use_mock_hardware = LaunchConfiguration("use_mock_hardware")
    use_rviz = LaunchConfiguration("use_rviz")

    robot_description_content = ParameterValue(
        Command(
            [
                PathJoinSubstitution([FindExecutable(name="xacro")]),
                " ",
                PathJoinSubstitution(
                    [FindPackageShare("mecanum_pico"), "urdf", "mecanum_robot.urdf.xacro"]
                ),
                " use_mock_hardware:=",
                use_mock_hardware,
            ]
        ),
        value_type=str,
    )
    robot_description = {"robot_description": robot_description_content}
    robot_controllers = PathJoinSubstitution(
        [FindPackageShare("mecanum_pico"), "config", "mecanum_controllers.yaml"]
    )
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("mecanum_pico"), "rviz", "mecanum_pico.rviz"]
    )

    # --------------------------------------------------------------------------
    # ros2_control_node
    # Husarion mecanum_drive_controller mit use_stamped_vel: false
    # subscribt bei use_stamped_vel=false direkt auf /cmd_vel (Twist).
    # Kein Remapping nötig — teleop_twist_keyboard funktioniert out-of-the-box.
    # --------------------------------------------------------------------------
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        output="both",
    )

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
        output="both",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(use_rviz),
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    mecanum_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["mecanum_drive_controller", "--controller-manager", "/controller_manager"],
    )

    delay_rviz = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[rviz_node],
        )
    )
    delay_mecanum_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[mecanum_controller_spawner],
        )
    )

    return LaunchDescription(
        [
            use_mock_hardware_arg,
            use_rviz_arg,
            control_node,
            robot_state_pub_node,
            joint_state_broadcaster_spawner,
            delay_rviz,
            delay_mecanum_controller,
        ]
    )
