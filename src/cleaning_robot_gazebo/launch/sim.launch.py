"""Start Gazebo Sim with the indoor house, spawn the cleaning robot and bridge topics to ROS 2.

Usage:
    ros2 launch cleaning_robot_gazebo sim.launch.py
    ros2 launch cleaning_robot_gazebo sim.launch.py rviz:=true x:=3.0 y:=2.0 yaw:=1.57
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    gazebo_share = get_package_share_directory('cleaning_robot_gazebo')
    description_share = get_package_share_directory('cleaning_robot_description')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(description_share, 'urdf', 'cleaning_robot.urdf.xacro')
    bridge_config = os.path.join(gazebo_share, 'config', 'ros_gz_bridge.yaml')
    rviz_config = os.path.join(gazebo_share, 'config', 'sim.rviz')

    world = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('rviz')
    x, y, yaw = LaunchConfiguration('x'), LaunchConfiguration('y'), LaunchConfiguration('yaw')

    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # -r: start the simulation running immediately
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-r -v 3 ', world],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'cleaning_robot',
            '-topic', 'robot_description',
            '-x', x, '-y', y, '-z', '0.02', '-Y', yaw,
        ],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config, 'use_sim_time': True}],
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution([gazebo_share, 'worlds', 'indoor_house.sdf']),
            description='Full path to the Gazebo world (.sdf)'),
        DeclareLaunchArgument('rviz', default_value='false',
                              description='Also open RViz (odom frame view)'),
        DeclareLaunchArgument('x', default_value='-2.0', description='Spawn x (m)'),
        DeclareLaunchArgument('y', default_value='0.0', description='Spawn y (m)'),
        DeclareLaunchArgument('yaw', default_value='0.0', description='Spawn yaw (rad)'),
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz,
    ])
