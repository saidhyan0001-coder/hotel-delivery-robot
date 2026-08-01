from setuptools import setup
import os

package_name = 'hotel_robot_perception'

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
    description='Perception nodes for ceiling AprilTag detection and room verification',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ceiling_apriltag_detector = hotel_robot_perception.ceiling_apriltag_detector:main',
        ],
    },
)
