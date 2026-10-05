from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            output='screen',
        ),
        Node(
            package='g18_prii3_turtlesim',
            executable='draw_18_node',
            name='draw_18_node',
            output='screen',
        ),
    ])

