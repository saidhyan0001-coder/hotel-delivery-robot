from setuptools import setup
import os

package_name = 'vapi_llm_interface'

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
    description='Vapi AI Webhook Bridge and Local Edge TinyLlama Interface for ROS 2 Nav2 Action Dispatching',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vapi_ros_bridge_node = vapi_llm_interface.vapi_ros_bridge_node:main',
        ],
    },
)
