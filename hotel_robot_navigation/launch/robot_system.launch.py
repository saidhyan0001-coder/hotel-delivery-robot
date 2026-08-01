import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_description = get_package_share_directory('hotel_robot_description')
    pkg_navigation = get_package_share_directory('hotel_robot_navigation')
    pkg_nav2 = get_package_share_directory('nav2_bringup')

    nav2_params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')
    ekf_params_file = os.path.join(pkg_navigation, 'config', 'ekf.yaml')

    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    # 1. Robot Description (URDF & State Publisher)
    launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_description, 'launch', 'description.launch.py')
        )
    )

    # 2. Hardware Driver Nodes
    node_motor_driver = Node(
        package='hotel_robot_hardware',
        executable='motor_encoder_driver_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    node_ultrasonic_driver = Node(
        package='hotel_robot_hardware',
        executable='ultrasonic_driver_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    node_imu_driver = Node(
        package='hotel_robot_hardware',
        executable='mpu6050_imu_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 3. EKF Odometry & IMU Sensor Fusion Node
    node_ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params_file, {'use_sim_time': use_sim_time}]
    )

    # 4. Ceiling AprilTag Perception Node
    node_apriltag = Node(
        package='hotel_robot_perception',
        executable='ceiling_apriltag_detector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 5. Vapi AI & LLM Interface Node
    node_vapi_bridge = Node(
        package='vapi_llm_interface',
        executable='vapi_ros_bridge_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 6. Nav2 Stack Bringup
    launch_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params_file,
            'autostart': 'true'
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false', description='Use simulation time if true'),
        launch_description,
        node_motor_driver,
        node_ultrasonic_driver,
        node_imu_driver,
        node_ekf,
        node_apriltag,
        node_vapi_bridge,
        launch_nav2
    ])
