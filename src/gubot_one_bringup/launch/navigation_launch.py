# Navigations Launch File für Nav2
# Startet alle Nav2-Komponenten für autonome Navigation (Planner, Controller, Recovery)
#
# Copyright (c) 2018 Intel Corporation
# Licensed under the Apache License, Version 2.0
#
# Launch-File Struktur:
# 1. Imports - Benötigte Python-Module
# 2. LaunchConfiguration - Variablen für Launch-Argumente
# 3. DeclareLaunchArgument - Definiere konfigurierbare Parameter
# 4. Nodes - ROS2-Knoten die gestartet werden
# 5. LaunchDescription - Rückgabe aller Komponenten

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Hole Launch-Verzeichnis
    bringup_dir = get_package_share_directory('gubot_one_bringup')

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    default_bt_xml_filename = LaunchConfiguration('default_bt_xml_filename')  # Behavior Tree XML
    map_subscribe_transient_local = LaunchConfiguration('map_subscribe_transient_local')

    # Lifecycle-Knoten für Navigation Stack
    lifecycle_nodes = ['controller_server',  # Folgt geplanten Pfaden
                       'planner_server',     # Berechnet globale Pfade
                       'recoveries_server',  # Führt Recovery-Behaviors aus
                       'bt_navigator',       # Behavior Tree Navigator (Koordination)
                       'waypoint_follower']  # Folgt Waypoint-Listen

    # Mappe vollqualifizierte Namen auf relative Namen (für Namespace-Unterstützung)
    # TF-Remapping notwendig für korrekte Transform-Verarbeitung
    remappings = [('/tf', 'tf'),
                  ('/tf_static', 'tf_static')]

    # Erstelle temporäre YAML-Dateien mit Substitutionen
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'default_bt_xml_filename': default_bt_xml_filename,
        'autostart': autostart,
        'map_subscribe_transient_local': map_subscribe_transient_local}

    configured_params = RewrittenYaml(
            source_file=params_file,
            root_key=namespace,
            param_rewrites=param_substitutions,
            convert_types=True)

    return LaunchDescription([
        # Setze Umgebungsvariable für sofortige Ausgabe von Log-Nachrichten
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Top-level namespace'),  # Namespace für alle Knoten

        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation (Gazebo) clock if true'),  # Simulationszeit oder echte Zeit

        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically startup the nav2 stack'),  # Automatischer Start der Lifecycle-Knoten

        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(bringup_dir, 'config', 'nav2_params.yaml'),
            description='Full path to the ROS2 parameters file to use'),  # Nav2-Parameter-Datei

        DeclareLaunchArgument(
            'default_bt_xml_filename',
            default_value=os.path.join(
                get_package_share_directory('nav2_bt_navigator'),
                'behavior_trees', 'navigate_w_replanning_and_recovery.xml'),
            description='Full path to the behavior tree xml file to use'),  # Behavior Tree für Navigation

        DeclareLaunchArgument(
            'map_subscribe_transient_local', default_value='false',
            description='Whether to set the map subscriber QoS to transient local'),  # QoS-Einstellung für Karten-Topic

        Node(
            package='nav2_controller',
            executable='controller_server',
            output='screen',
            parameters=[configured_params],  # Controller Server - Folgt geplanten Pfaden (z.B. DWB, TEB)
            remappings=remappings),

        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params],  # Planner Server - Berechnet globale Pfade (z.B. NavFn, Smac)
            remappings=remappings),

        Node(
            package='nav2_recoveries',
            executable='recoveries_server',
            name='recoveries_server',
            output='screen',
            parameters=[configured_params],  # Recovery Server - Führt Recovery-Behaviors aus (Spin, Backup)
            remappings=remappings),

        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params],  # BT Navigator - Koordiniert Navigation mit Behavior Trees
            remappings=remappings),

        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params],  # Waypoint Follower - Folgt Liste von Waypoints
            remappings=remappings),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': lifecycle_nodes}]),  # Verwaltet Lifecycle-States der Navigations-Knoten

    ])
