# Autonomous Hotel Delivery Robot: ROS 2 System Architecture & Master Guide

An end-to-end, production-grade ROS 2 system (compatible with **ROS 2 Humble & Jazzy**) for an **Autonomous Hotel Delivery Robot**. Features differential drive kinematics, 2D LiDAR SLAM, 3x Ultrasonic obstacle costmap layers, upward-facing AprilTag ceiling room verification, IMU sensor fusion (`robot_localization`), dynamic voice HRI via **Vapi AI Webhooks**, local on-device **TinyLlama / Ollama LLM fallback**, 3D **Gazebo simulation**, and an **Interactive 2D Desktop GUI Simulator**.

---

## 📋 Table of Contents
1. [Prerequisites & System Installation (Start to End)](#1-prerequisites--system-installation-start-to-end)
2. [Hardware Architecture & Wiring Reference](#2-hardware-architecture--wiring-reference)
3. [Workspace Setup & Building](#3-workspace-setup--building)
4. [One-Click Automated Builder & Launcher](#4-one-click-automated-builder--launcher)
5. [Execution Commands (Simulations & Hardware)](#5-execution-commands-simulations--hardware)
6. [Individual Node Launch Commands](#6-individual-node-launch-commands)
7. [Voice Intent Webhook & LLM Testing (curl)](#7-voice-intent-webhook--llm-testing-curl)
8. [ROS 2 Verification & Inspection Commands](#8-ros-2-verification--inspection-commands)

---

## 1. Prerequisites & System Installation (Start to End)

Follow these step-by-step terminal commands on a fresh **Ubuntu 22.04 LTS (Jammy)** installation (Raspberry Pi 4/5 or PC):

### Step 1.1: System Updates & Essential Tools
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl gnupg lsb-release git python3-pip
```

### Step 1.2: Install ROS 2 Humble Desktop
```bash
# Add ROS 2 GPG Key
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# Add ROS 2 Repository to Sources List
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Update Package Index
sudo apt update

# Install ROS 2 Humble Desktop & Build Utilities
sudo apt install -y \
    ros-humble-desktop \
    python3-colcon-common-extensions \
    python3-rosdep
```

### Step 1.3: Install System & ROS 2 Package Dependencies
```bash
sudo apt install -y \
    ros-humble-nav2-bringup \
    ros-humble-nav2-costmap-2d \
    ros-humble-nav2-planner \
    ros-humble-nav2-controller \
    ros-humble-nav2-dwb-controller \
    ros-humble-nav2-amcl \
    ros-humble-nav2-bt-navigator \
    ros-humble-robot-localization \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-cv-bridge \
    ros-humble-vision-opencv
```

### Step 1.4: Install Python Libraries & Drivers
```bash
pip3 install \
    smbus2 \
    opencv-python \
    numpy \
    aiohttp \
    requests \
    pupil-apriltags \
    RPi.GPIO \
    gpiozero
```

### Step 1.5: Environment Auto-Sourcing Configuration
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 2. Hardware Architecture & Wiring Reference

### Differential Drive Kinematics Parameters
- **Chassis Footprint:** $0.35\,\text{m} \times 0.35\,\text{m} \times 0.80\,\text{m}$
- **Wheel Radius ($R$):** $0.05\,\text{m}$ ($10\,\text{cm}$ diameter)
- **Track Width ($L$):** $0.30\,\text{m}$ (Distance between drive wheel contact points)
- **Differential Kinematics Equations:**
  $$\omega_R = \frac{v + \omega \cdot \frac{L}{2}}{R}, \quad \omega_L = \frac{v - \omega \cdot \frac{L}{2}}{R}$$

### L298N Dual H-Bridge Motor Driver (BCM GPIO Pins)
- **Left Motor:** `ENA` -> GPIO 12 (PWM), `IN1` -> GPIO 5, `IN2` -> GPIO 6
- **Right Motor:** `ENB` -> GPIO 13 (PWM), `IN3` -> GPIO 13, `IN4` -> GPIO 19

### Quadrature Encoders (BCM GPIO Pins)
- **Left Wheel Encoder:** Phase A -> GPIO 17, Phase B -> GPIO 27
- **Right Wheel Encoder:** Phase A -> GPIO 22, Phase B -> GPIO 23

### HC-SR04 Ultrasonic Sensors (BCM GPIO Pins)
- **Front-Left:** Trigger -> GPIO 5, Echo -> GPIO 6 (`ultrasonic_fl_link`)
- **Front-Center:** Trigger -> GPIO 13, Echo -> GPIO 19 (`ultrasonic_fc_link`)
- **Front-Right:** Trigger -> GPIO 26, Echo -> GPIO 21 (`ultrasonic_fr_link`)

### MPU6050 / BNO055 IMU Sensor (I2C Bus 1)
- `SDA` -> GPIO 2, `SCL` -> GPIO 3 (I2C Address `0x68`)

### Cameras & LiDAR
- **2D LiDAR Scanner:** Mounted at $z=0.20\,\text{m}$ height (`laser_frame`), USB `/dev/ttyUSB0`
- **Ceiling AprilTag Camera:** Upward-facing USB camera `/dev/video0` (`ceiling_camera_link`)

---

## 3. Workspace Setup & Building

```bash
# 1. Clone Workspace Repository
git clone https://github.com/saidhyan0001-coder/hotel-delivery-robot.git
cd hotel-delivery-robot

# 2. Build Workspace with colcon
colcon build --symlink-install

# 3. Source Workspace Overlay
source install/setup.bash
```

---

## 4. One-Click Automated Builder & Launcher

For effortless building and execution on Linux, run our interactive automated bash script:

```bash
chmod +x run_ros2_humble.sh
./run_ros2_humble.sh
```

---

## 5. Execution Commands (Simulations & Hardware)

### Option A: Interactive 2D Desktop GUI Simulator (Cross-Platform / Windows / Linux)
Launches top-down 2D floorplan visualizer with animated LiDAR rays, ultrasonic beams, and click-to-dispatch voice goal buttons:
```bash
python3 gui_sim_runner.py
```

### Option B: Standalone Console Test Runner
Runs differential drive kinematics integration, Vapi AI webhook server, and Nav2 goal execution in pure Python:
```bash
python3 standalone_sim_runner.py
```

### Option C: 3D Gazebo Simulation (Linux ROS 2)
Launches 3D Gazebo hotel corridor world (`hotel_corridor.world`), spawns URDF robot entity, EKF sensor fusion, AprilTag perception, Vapi bridge, and Nav2 stack:
```bash
ros2 launch hotel_robot_navigation gazebo_simulation.launch.py
```

### Option D: Physical Robot Hardware Launch (Raspberry Pi)
Brings up live L298N motor drivers, encoders, HC-SR04 rangefinders, IMU, AprilTag detector, Vapi bridge, and Nav2 on real hardware:
```bash
ros2 launch hotel_robot_navigation robot_system.launch.py
```

---

## 6. Individual Node Launch Commands

```bash
# 1. Robot Description (State Publisher + URDF)
ros2 launch hotel_robot_description description.launch.py

# 2. Motor & Encoder Hardware Driver Node
ros2 run hotel_robot_hardware motor_encoder_driver_node

# 3. 3x HC-SR04 Ultrasonic Sensor Driver Node
ros2 run hotel_robot_hardware ultrasonic_driver_node

# 4. MPU6050 IMU Driver Node
ros2 run hotel_robot_hardware mpu6050_imu_node

# 5. Ceiling AprilTag Perception Node
ros2 run hotel_robot_perception ceiling_apriltag_detector

# 6. Vapi AI Webhook Bridge & Local LLM Node
ros2 run vapi_llm_interface vapi_ros_bridge_node
```

---

## 7. Voice Intent Webhook & LLM Testing (curl)

### 1. Primary Vapi AI Voice Webhook Request (Target: Room 304)
```bash
curl -X POST http://localhost:8080/vapi_webhook \
     -H "Content-Type: application/json" \
     -d '{"message": {"intent": "deliver", "parameters": {"room": "Room 304"}}}'
```

### 2. Secondary Offline Voice Prompt Request (TinyLlama / Ollama Fallback)
```bash
curl -X POST http://localhost:8080/voice_prompt \
     -H "Content-Type: application/json" \
     -d '{"text": "Please bring extra towels to Room 302"}'
```

### 3. Query Real-Time Robot Status & Distance Remaining
```bash
curl http://localhost:8080/status
```

---

## 8. ROS 2 Verification & Inspection Commands

```bash
# Check Active ROS 2 Topics
ros2 topic list

# Inspect Odometry Output
ros2 topic echo /odom

# Inspect LiDAR Scan Data
ros2 topic echo /scan

# Inspect Front-Center Ultrasonic Range Sensor
ros2 topic echo /ultrasonic/front_center

# Inspect IMU Raw Acceleration & Gyroscope
ros2 topic echo /imu/data_raw

# Inspect Ceiling AprilTag Detected Room
ros2 topic echo /apriltag/detected_room

# Call Room Arrival Verification Service
ros2 service call /verify_room_arrival std_srvs/srv/Trigger
```
