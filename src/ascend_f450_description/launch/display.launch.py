from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pkg_share = get_package_share_directory(
        'ascend_f450_description'
    )

    urdf_file = os.path.join(
        pkg_share,
        'urdf',
        'drone_model.urdf'
    )

    rviz_config = os.path.join(
        pkg_share,
        'config',
        'drone_rviz.rviz'
    )

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()

    return LaunchDescription([

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc
            }]
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui'
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom',
            arguments=[
                '--x', '0',
                '--y', '0',
                '--z', '0',
                '--roll', '0',
                '--pitch', '0',
                '--yaw', '0',
                '--frame-id', 'map',
                '--child-frame-id', 'odom'
            ]
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='odom_to_base',
            arguments=[
                '--x', '0',
                '--y', '0',
                '--z', '0.5',
                '--roll', '0',
                '--pitch', '0',
                '--yaw', '0',
                '--frame-id', 'odom',
                '--child-frame-id', 'base_link'
            ]
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config]
        )

    ])
