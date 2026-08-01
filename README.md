# Autonomous Hotel Delivery Robot: ROS 2 System Architecture & Complete Command Guide

This repository contains the complete production-grade ROS 2 software stack, hardware drivers, perception systems, conversational AI bridge, Gazebo simulation environment, interactive 2D GUI simulator, and navigation configuration for an **Autonomous Hotel Delivery Robot** built on ROS 2 (Humble / Jazzy).

---

## 1. System Overview & Hardware Kinematics

- **Chassis Footprint:** $0.35\,\text{m} \times 0.35\,\text{m} \times 0.80\,\text{m}$
- **Wheel Radius ($R$):** $0.05\,\text{m}$ ($10\,\text{cm}$ diameter)
- **Track Width ($L$):** $0.30\,\text{m}$ (Distance between drive wheel contact points)
- **Differential Drive Kinematics:**
  $$\omega_R = \frac{v + \omega \cdot \frac{L}{2}}{R}, \quad \omega_L = \frac{v - \omega \cdot \frac{L}{2}}{R}$$
- **Compute Platform:** Raspberry Pi 4 (8GB) / Pi 5 running Ubuntu Server + ROS 2.

---

## 2. Hardware Wiring Reference

### L298N Dual H-Bridge Motor Driver
- **Left Motor:** `ENA` -> GPIO 12 (PWM), `IN1` -> GPIO 5, `IN2` -> GPIO 6
- **Right Motor:** `ENB` -> GPIO 13 (PWM), `IN3` -> GPIO 13, `IN4` -> GPIO 19

### Quadrature Encoders
- **Left Encoder:** Phase A -> GPIO 17, Phase B -> GPIO 27
- **Right Encoder:** Phase A -> GPIO 22, Phase B -> GPIO 23

### HC-SR04 Ultrasonic Sensors
- **Front-Left:** Trigger -> GPIO 5, Echo -> GPIO 6 (`ultrasonic_fl_link`)
- **Front-Center:** Trigger -> GPIO 13, Echo -> GPIO 19 (`ultrasonic_fc_link`)
- **Front-Right:** Trigger -> GPIO 26, Echo -> GPIO 21 (`ultrasonic_fr_link`)

### MPU6050 / BNO055 IMU Sensor
- **I2C Bus 1:** `SDA` -> GPIO 2, `SCL` -> GPIO 3 (I2C Address `0x68`)

### Cameras & LiDAR
- **2D LiDAR Scanner:** USB `/dev/ttyUSB0` mounted at $z=0.20\,\text{m}$ height (`laser_frame`)
- **Ceiling AprilTag Camera:** Upward USB camera `/dev/video0` (`ceiling_camera_link`)

---

## 3. Installation & Workspace Setup

```bash
# 1. Install ROS 2 Dependencies (Desktop Full)
sudo apt update
sudo apt install -y ros-humble-desktop ros-humble-nav2-bringup ros-humble-robot-localization ros-humble-gazebo-ros-pkgs

# 2. Clone Workspace
git clone https://github.com/saidhyan0001-coder/hotel-delivery-robot.git
cd hotel-delivery-robot

# 3. Install Python Dependencies
pip install rclpy smbus2 opencv-python numpy aiohttp

# 4. Build ROS 2 Packages
colcon build --symlink-install
source install/setup.bash
```

---

## 4. Execution Commands

### Option A: Interactive 2D Desktop GUI Simulator (Cross-Platform / Windows / Linux)
Launch real-time 2D floorplan visualization with animated LiDAR rays, ultrasonic beams, and click-to-dispatch buttons:
```bash
python gui_sim_runner.py
```

### Option B: Standalone Console Test Runner
Simulates kinematics integration, Vapi AI webhook server, and Nav2 goal execution without ROS 2 binaries:
```bash
python standalone_sim_runner.py
```

### Option C: Full 3D Gazebo Simulation
Launches 3D Gazebo hotel corridor world, spawns URDF robot entity, EKF sensor fusion, AprilTag perception, Vapi bridge, and Nav2 stack:
```bash
ros2 launch hotel_robot_navigation gazebo_simulation.launch.py
```

### Option D: Physical Robot Hardware Launch (Raspberry Pi)
Brings up live L298N motor drivers, encoders, HC-SR04 rangefinders, IMU, AprilTag detector, Vapi bridge, and Nav2 on real hardware:
```bash
ros2 launch hotel_robot_navigation robot_system.launch.py
```

---

## 5. Launch Individual ROS 2 Nodes

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

## 6. HRI Voice Intent Webhook Testing (`curl` Commands)

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

## 7. ROS 2 Verification & Inspection Commands

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
