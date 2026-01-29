#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    
    # Namespace to separate real camera from simulated one
    camera_namespace = LaunchConfiguration('camera_namespace')
    
    camera_namespace_arg = DeclareLaunchArgument(
        'camera_namespace',
        default_value='real_camera',
        description='Namespace for the real USB camera topics'
    )
    
    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        # namespace='real_camera',  # Temporarily disabled - might cause crash
        output='screen',
        parameters=[{
            'video_device': '/dev/video0',
            'pixel_format': 'yuyv',
            'output_encoding': 'rgb8',
            'image_width': 640,
            'image_height': 480,
            'framerate': 15.0,
            'camera_name': 'real_cam',
            'camera_frame_id': 'camera_link_optical',
        }]
    )
    
    return LaunchDescription([
        camera_namespace_arg,
        usb_cam_node
    ])
