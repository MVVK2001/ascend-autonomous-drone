from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='ascend_core',
            executable='mission_manager',
            name='mission_manager',
            output='screen'
        ),

        Node(
            package='ascend_navigation',
            executable='navigation_node',
            name='navigation_node',
            output='screen'
        ),

        Node(
            package='ascend_telemetry',
            executable='telemetry_node',
            name='telemetry_node',
            output='screen'
        ),
        
        Node(
            package='ascend_vision',
            executable='vision_node',
            name='vision_node',
            output='screen'
        ),

    ])
