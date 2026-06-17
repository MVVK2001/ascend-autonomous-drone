from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='ascend_vision',
            executable='camera_node',
            name='camera_node',
            output='screen'
        ),

        Node(
            package='ascend_vision',
            executable='vision_node',
            name='vision_node',
            output='screen'
        ),

        Node(
            package='ascend_telemetry',
            executable='telemetry_node',
            name='telemetry_node',
            output='screen'
        ),

        Node(
            package='ascend_transfer',
            executable='data_transfer_node',
            name='data_transfer_node',
            output='screen'
        ),

    ])
