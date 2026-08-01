import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_description = get_package_share_directory('hotel_robot_description')
    pkg_navigation = get_package_share_directory('hotel_robot_navigation')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_nav2 = get_package_share_directory('nav2_bringup')

    world_file = os.path.join(pkg_navigation, 'worlds', 'hotel_corridor.world')
    nav2_params_file = os.path.join(pkg_navigation, 'config', 'nav2_params.yaml')
    ekf_params_file = os.path.join(pkg_navigation, 'config', 'ekf.yaml')

    # Parse URDF/Xacro
    xacro_file = os.path.join(pkg_description, 'urdf', 'hotel_robot.urdf.xacro')
    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc)
    robot_description_config = doc.toxml()

    # Launch Configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # 1. Gazebo Server & Client
    launch_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_file}.items()
    )

    # 2. Robot State Publisher Node
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_config, 'use_sim_time': use_sim_time}]
    )

    # 3. Spawn Robot Entity in Gazebo
    node_spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'hotel_robot', '-x', '0.0', '-y', '0.0', '-z', '0.05'],
        output='screen'
    )

    # 4. EKF Sensor Fusion Node
    node_ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params_file, {'use_sim_time': use_sim_time}]
    )

    # 5. Ceiling AprilTag Perception Node
    node_apriltag = Node(
        package='hotel_robot_perception',
        executable='ceiling_apriltag_detector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 6. Vapi AI & LLM Interface Node
    node_vapi_bridge = Node(
        package='vapi_llm_interface',
        executable='vapi_ros_bridge_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 7. Nav2 Stack Bringup
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
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use Gazebo sim time'),
        launch_gazebo,
        node_robot_state_publisher,
        node_spawn_entity,
        node_ekf,
        node_apriltag,
        node_vapi_bridge,
        launch_nav2
    ])
