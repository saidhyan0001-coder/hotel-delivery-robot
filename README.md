# Autonomous Hotel Delivery Robot: ROS 2 System Architecture

This repository contains the complete production-grade ROS 2 software stack, hardware integration drivers, perception system, conversational AI bridge, and navigation stack for an **Autonomous Hotel Delivery Robot**.

---

## 1. System Architecture & Kinematics

- **Robot Footprint:** $0.35\,\text{m} \times 0.35\,\text{m} \times 0.80\,\text{m}$
- **Wheel Radius ($R$):** $0.05\,\text{m}$ ($10\,\text{cm}$ diameter)
- **Track Width ($L$):** $0.30\,\text{m}$
- **Differential Drive Kinematics:**
  $$\omega_R = \frac{v + \omega \cdot (L / 2)}{R}, \quad \omega_L = \frac{v - \omega \cdot (L / 2)}{R}$$
- **Compute Platform:** Raspberry Pi 4 / 5 running Ubuntu Server + ROS 2 (Humble / Jazzy).

---

## 2. Package Breakdown

| Package Name | Description | Key Components |
|---|---|---|
| [`hotel_robot_description`](file:///c:/Users/Dhyan/Downloads/major/hotel_robot_description) | URDF / Xacro Robot Model | Chassis box ($35\times35\times80\,\text{cm}$), 2D LiDAR frame, upward camera, front camera, 3x Ultrasonic frames, IMU frame. |
| [`hotel_robot_hardware`](file:///c:/Users/Dhyan/Downloads/major/hotel_robot_hardware) | Low-level C++/Python Drivers | L298N PWM motor controller, Quadrature Encoder odometry & TF publisher, 3x HC-SR04 ultrasonic range publishers, MPU6050 IMU publisher. |
| [`hotel_robot_perception`](file:///c:/Users/Dhyan/Downloads/major/hotel_robot_perception) | Ceiling AprilTag Verification | Upward camera tag processing, Tag ID to room mapping (e.g. Tag 12 -> Room 304), `/verify_room_arrival` service. |
| [`vapi_llm_interface`](file:///c:/Users/Dhyan/Downloads/major/vapi_llm_interface) | Conversational AI HRI Bridge | Vapi AI HTTP Webhook listener, local TinyLlama / Ollama offline fallback engine, `NavigateToPose` Action Client dispatching. |
| [`hotel_robot_navigation`](file:///c:/Users/Dhyan/Downloads/major/hotel_robot_navigation) | Nav2 & Sensor Fusion Stack | `nav2_params.yaml` (AMCL, DWB/RPP, 2D LiDAR + Ultrasonic Costmaps), `ekf.yaml` (`robot_localization`), master `robot_system.launch.py`. |

---

## 3. Hardware Wiring Reference

### L298N Dual H-Bridge Motor Driver
- **Left Motor:** `ENA` -> GPIO 12 (PWM), `IN1` -> GPIO 5, `IN2` -> GPIO 6
- **Right Motor:** `ENB` -> GPIO 13 (PWM), `IN3` -> GPIO 13, `IN4` -> GPIO 19

### Quadrature Encoders
- **Left Encoder:** Phase A -> GPIO 17, Phase B -> GPIO 27
- **Right Encoder:** Phase A -> GPIO 22, Phase B -> GPIO 23

### HC-SR04 Ultrasonic Sensors
- **Front-Left:** Trigger -> GPIO 5, Echo -> GPIO 6
- **Front-Center:** Trigger -> GPIO 13, Echo -> GPIO 19
- **Front-Right:** Trigger -> GPIO 26, Echo -> GPIO 21

### MPU6050 IMU Sensor
- **I2C Bus 1:** `SDA` -> GPIO 2, `SCL` -> GPIO 3 (Address `0x68`)

---

## 4. Build & Launch Instructions

### 1. Build Workspace
```bash
cd ~/hotel_robot_ws
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch Full System (Hardware, EKF, Perception, Vapi Bridge, Nav2)
```bash
ros2 launch hotel_robot_navigation robot_system.launch.py
```

---

## 5. HRI Voice Intent Webhook Testing

### Primary Vapi AI Voice Webhook Request
```bash
curl -X POST http://localhost:8080/vapi_webhook \
     -H "Content-Type: application/json" \
     -d '{"message": {"intent": "deliver", "parameters": {"room": "Room 304"}}}'
```

### Secondary Offline Edge Prompt Request (TinyLlama / Ollama Fallback)
```bash
curl -X POST http://localhost:8080/voice_prompt \
     -H "Content-Type: application/json" \
     -d '{"text": "Please bring extra towels to Room 302"}'
```

### Check Navigation Status
```bash
curl http://localhost:8080/status
```
