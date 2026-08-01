from setuptools import setup
import os
from glob import glob

package_name = 'hotel_robot_hardware'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name] if os.path.exists('resource/' + package_name) else []),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=true,
    maintainer='Hotel Robot Team',
    maintainer_email='dev@hotelrobot.com',
    description='Low-level ROS 2 hardware drivers for L298N motors, encoders, ultrasonic sensors, and IMU',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_encoder_driver_node = hotel_robot_hardware.motor_encoder_driver_node:main',
            'ultrasonic_driver_node = hotel_robot_hardware.ultrasonic_driver_node:main',
            'mpu6050_imu_node = hotel_robot_hardware.mpu6050_imu_node:main',
        ],
    },
)
