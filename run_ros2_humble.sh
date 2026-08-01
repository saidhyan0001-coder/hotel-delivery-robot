#!/bin/bash
# ==============================================================================
# Autonomous Hotel Delivery Robot - One-Click ROS 2 Humble Linux Builder & Runner
# ==============================================================================

set -e

GREEN='\030[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}    AUTONOMOUS HOTEL DELIVERY ROBOT — ROS 2 HUMBLE LINUX BUILDER      ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Source ROS 2 Humble Setup
if [ -f "/opt/ros/humble/setup.bash" ]; then
    echo -e "${GREEN}[1/4] Sourcing ROS 2 Humble installation...${NC}"
    source /opt/ros/humble/setup.bash
elif [ -f "/opt/ros/jazzy/setup.bash" ]; then
    echo -e "${GREEN}[1/4] Sourcing ROS 2 Jazzy installation...${NC}"
    source /opt/ros/jazzy/setup.bash
else
    echo -e "${RED}[ERROR] ROS 2 setup.bash not found in /opt/ros/humble or /opt/ros/jazzy.${NC}"
    echo -e "${YELLOW}Please install ROS 2 Humble Desktop first: sudo apt install ros-humble-desktop${NC}"
    exit 1
fi

# 2. Install System & ROS 2 Dependencies
echo -e "${GREEN}[2/4] Verifying & installing ROS 2 dependencies...${NC}"
sudo apt update -qq || true
sudo apt install -y \
    ros-humble-nav2-bringup \
    ros-humble-nav2-costmap-2d \
    ros-humble-nav2-planner \
    ros-humble-nav2-controller \
    ros-humble-nav2-dwb-controller \
    ros-humble-robot-localization \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    python3-colcon-common-extensions \
    python3-pip

pip3 install smbus2 opencv-python numpy aiohttp --quiet || true

# 3. Build Workspace with colcon
echo -e "${GREEN}[3/4] Building workspace packages using colcon...${NC}"
colcon build --symlink-install

# 4. Source Built Workspace
echo -e "${GREEN}[4/4] Sourcing built workspace overlay...${NC}"
source install/setup.bash

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}             BUILD COMPLETED SUCCESSFULLY! READY TO LAUNCH            ${NC}"
echo -e "${GREEN}======================================================================${NC}"

echo -e "\nChoose launch mode:"
echo -e "  1) Launch 3D Gazebo Simulation (hotel_corridor.world + Nav2 + Vapi Bridge)"
echo -e "  2) Launch Physical Robot Hardware (L298N + Encoders + Ultrasonic + Nav2)"
echo -e "  3) Run 2D Desktop Interactive GUI Simulator (Python/Tkinter)"
echo -e "  4) Exit"

read -p "Select option [1-4]: " choice

case $choice in
    1)
        echo -e "${BLUE}Launching 3D Gazebo Simulation...${NC}"
        ros2 launch hotel_robot_navigation gazebo_simulation.launch.py
        ;;
    2)
        echo -e "${BLUE}Launching Physical Robot Hardware System...${NC}"
        ros2 launch hotel_robot_navigation robot_system.launch.py
        ;;
    3)
        echo -e "${BLUE}Launching 2D Desktop GUI Simulator...${NC}"
        python3 gui_sim_runner.py
        ;;
    4)
        echo -e "${YELLOW}Exiting.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option.${NC}"
        ;;
esac
