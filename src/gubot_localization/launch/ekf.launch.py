"""
EKF Localization Launch
=======================
Startet den robot_localization EKF-Knoten.
Referenz: rosbot_ws/src/rosbot_ros/rosbot_localization/launch/ekf.launch.py

Änderungen:
- use_sim_time Argument und per-Node-Parameter entfernt
  ALT: use_sim_time wurde per Node-Parameter gesetzt
  NEU: use_sim_time wird global durch SetParameter(use_sim_time=True) in simulation.launch.py
       gesetzt und propagiert automatisch an alle Nodes
- /diagnostics Remap hinzugefügt (Referenz-Pattern)
  ALT: fehlte
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_name = "gubot_localization"

    ekf_config = PathJoinSubstitution([
        FindPackageShare(package_name),
        "config",
        "ekf.yaml",
    ])

    # ALT: use_sim_time wurde hier per Node-Parameter gesetzt
    # NEU: use_sim_time kommt vom globalen SetParameter in simulation.launch.py
    robot_localization_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_node",
        parameters=[ekf_config],
        # NEU: /diagnostics Remap wie Referenz
        remappings=[("/diagnostics", "diagnostics")],
    )

    return LaunchDescription([
        robot_localization_node,
    ])
