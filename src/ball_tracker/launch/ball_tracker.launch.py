"""
Ball Tracker Launch - Ball-Erkennung und Verfolgung
====================================================
Startet Nodes für Ball-Erkennung und autonome Verfolgung

Komponenten:
1. detect_ball - Erkennt Ball in Kamerabild (OpenCV)
2. detect_ball_3d - 3D Position des Balls (optional)
3. follow_ball - Steuert Roboter um Ball zu folgen

Launch Arguments:
- params_file: Pfad zu Parameter-Datei
- detect_only: false - Nur Erkennung, keine Verfolgung
- follow_only: false - Nur Verfolgung (für Tests mit manuellen Detections)
- tune_detection: false - Tuning-Modus für Erkennung (zeigt Schwellwerte)
- use_sim_time: false - Simulationszeit verwenden
- image_topic: '/camera/image_raw' - Kamera-Bild Topic
- cmd_vel_topic: '/cmd_vel' - Geschwindigkeits-Befehl Topic
- enable_3d_tracker: false - 3D Tracker aktivieren

Verwendung:
  ros2 launch ball_tracker ball_tracker.launch.py
  ros2 launch ball_tracker ball_tracker.launch.py tune_detection:=true
  ros2 launch ball_tracker ball_tracker.launch.py detect_only:=true
  ros2 launch ball_tracker ball_tracker.launch.py enable_3d_tracker:=true

Aufbau:
1. DeclareLaunchArgument - Alle konfigurierbaren Parameter
2. Nodes mit Conditions - Starten nur wenn Bedingung erfüllt
3. UnlessCondition - Node startet NICHT wenn Bedingung true
4. IfCondition - Node startet NUR wenn Bedingung true
"""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # Launch Configuration Variablen
    params_file = LaunchConfiguration('params_file')
    params_file_dec = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(get_package_share_directory('ball_tracker'),'config','ball_tracker_params_example.yaml'),
        description='Full path to params file for all ball_tracker nodes.')

    detect_only = LaunchConfiguration('detect_only')
    detect_only_dec = DeclareLaunchArgument(
        'detect_only',
        default_value='false',
        description='Doesn\'t run the follow component. Useful for just testing the detections.')
    
    follow_only = LaunchConfiguration('follow_only')
    follow_only_dec = DeclareLaunchArgument(
        'follow_only',
        default_value='false',
        description='Doesn\'t run the detect component. Useful for testing just the following. (e.g. with manually published detections)')
    
    tune_detection = LaunchConfiguration('tune_detection')
    tune_detection_dec = DeclareLaunchArgument(
    'tune_detection',
    default_value='false',
    description='Enables tuning mode for the detection')
    
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim_time_dec = DeclareLaunchArgument(
    'use_sim_time',
    default_value='false',
    description='Enables sim time for the follow node.')
    
    image_topic = LaunchConfiguration('image_topic')
    image_topic_dec = DeclareLaunchArgument(
        'image_topic',
        default_value='/camera/image_raw',
        description='The name of the input image topic.')

    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    cmd_vel_topic_dec = DeclareLaunchArgument(
    'cmd_vel_topic',
    default_value='/cmd_vel',
    description='The name of the output command vel topic.')

    enable_3d_tracker = LaunchConfiguration('enable_3d_tracker')
    enable_3d_tracker_dec = DeclareLaunchArgument(
    'enable_3d_tracker',
    default_value='false',
    description='Enables the 3D tracker node')


    # Node 1: Ball Erkennung (2D)
    # Läuft NICHT wenn follow_only=true
    detect_node = Node(
            package='ball_tracker',
            executable='detect_ball',
            parameters=[params_file, {'tuning_mode': tune_detection}],
            remappings=[('/image_in',image_topic)],  # Kamera-Bild Input
            condition=UnlessCondition(follow_only)  # Startet NICHT wenn follow_only
         )

    # Node 2: Ball Erkennung (3D)
    # Läuft NUR wenn enable_3d_tracker=true
    detect_3d_node = Node(
            package='ball_tracker',
            executable='detect_ball_3d',
            parameters=[params_file],
            condition=IfCondition(enable_3d_tracker)  # Startet NUR wenn aktiviert
         )

    # Node 3: Ball Verfolgung
    # Läuft NICHT wenn detect_only=true
    follow_node = Node(
            package='ball_tracker',
            executable='follow_ball',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            remappings=[('/cmd_vel',cmd_vel_topic)],  # Geschwindigkeits-Output
            condition=UnlessCondition(detect_only)  # Startet NICHT wenn detect_only
         )


    # Launch Description mit allen Arguments und Nodes
    return LaunchDescription([
        # Arguments
        params_file_dec,
        detect_only_dec,
        follow_only_dec,
        tune_detection_dec,
        use_sim_time_dec,
        image_topic_dec,
        cmd_vel_topic_dec,
        enable_3d_tracker_dec,
        # Nodes
        detect_node,
        detect_3d_node,
        follow_node,    
    ])
