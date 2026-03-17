# Lokalisierungs Launch File für Nav2 (AMCL)
# Startet Map Server und AMCL für Roboter-Lokalisierung in bekannter Karte
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
    map_yaml_file = LaunchConfiguration('map')  # Pfad zur Karten-YAML-Datei
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    lifecycle_nodes = ['map_server', 'amcl']  # Lifecycle-Knoten für Manager

    # Mappe vollqualifizierte Namen auf relative Namen (für Namespace-Unterstützung)
    # TF-Remapping notwendig für korrekte Transform-Verarbeitung
    remappings = [('/tf', 'tf'),
                  ('/tf_static', 'tf_static')]

    # Erstelle temporäre YAML-Dateien mit Substitutionen
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file}  # Karten-Datei für Map Server

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
            'map',
            default_value=os.path.join(bringup_dir, 'maps', 'turtlebot3_world.yaml'),
            description='Full path to map yaml file to load'),  # Karten-Datei (YAML mit Bild-Referenz)

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

        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[configured_params],  # Lädt und publiziert Karte auf /map Topic
            remappings=remappings),

        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[configured_params],  # AMCL (Adaptive Monte Carlo Localization) für Positionsschätzung
            remappings=remappings),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time},
                        {'autostart': autostart},
                        {'node_names': lifecycle_nodes}])  # Verwaltet Lifecycle-States der Knoten
    ])
