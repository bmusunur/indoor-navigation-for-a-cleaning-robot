"""Run SLAM Toolbox (online async) and RViz against the running simulation.

Start the simulation first in another terminal:
    ros2 launch cleaning_robot_gazebo sim.launch.py

Or start everything at once:
    ros2 launch cleaning_robot_slam slam.launch.py sim:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    slam_share = get_package_share_directory('cleaning_robot_slam')
    gazebo_share = get_package_share_directory('cleaning_robot_gazebo')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')

    slam_params = LaunchConfiguration('slam_params_file')
    use_rviz = LaunchConfiguration('rviz')
    start_sim = LaunchConfiguration('sim')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_share, 'launch', 'sim.launch.py')),
        condition=IfCondition(start_sim),
    )

    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_share, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'use_sim_time': 'true',
            'slam_params_file': slam_params,
        }.items(),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(slam_share, 'rviz', 'slam.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(slam_share, 'config', 'mapper_params_online_async.yaml'),
            description='SLAM Toolbox parameter file'),
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz'),
        DeclareLaunchArgument('sim', default_value='false',
                              description='Also start Gazebo + robot (sim.launch.py)'),
        sim,
        slam_toolbox,
        rviz,
    ])
