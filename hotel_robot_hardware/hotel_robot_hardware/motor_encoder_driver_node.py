#!/usr/bin/env python3
"""
Motor & Encoder Driver Node for Autonomous Hotel Delivery Robot
Differential Drive Kinematics, L298N Motor Driver, Quadrature Encoder Processing, and Odometry Publisher.
"""

import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

# Hardware Abstraction Layer for GPIO
GPIO_AVAILABLE = False
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False


def euler_to_quaternion(roll, pitch, yaw):
    qx = math.sin(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) - math.cos(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
    qy = math.cos(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2) + math.sin(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2)
    qz = math.cos(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2) - math.sin(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2)
    qw = math.cos(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) + math.sin(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
    return Quaternion(x=qx, y=qy, z=qz, w=qw)


class MotorEncoderDriverNode(Node):

    def __init__(self):
        super().__init__('motor_encoder_driver_node')

        # Declare Kinematic & Hardware Parameters
        self.declare_parameter('wheel_radius', 0.05)       # meters (10 cm diameter)
        self.declare_parameter('track_width', 0.30)        # meters (distance between wheel centers)
        self.declare_parameter('encoder_ppr', 360)         # pulses per revolution
        self.declare_parameter('max_wheel_speed', 1.5)     # m/s
        self.declare_parameter('publish_tf', True)

        # L298N Pin Assignment (BCM Pin Numbers)
        self.declare_parameter('left_motor_ena', 12)
        self.declare_parameter('left_motor_in1', 5)
        self.declare_parameter('left_motor_in2', 6)
        self.declare_parameter('right_motor_enb', 13)
        self.declare_parameter('right_motor_in3', 13)
        self.declare_parameter('right_motor_in4', 19)

        # Quadrature Encoder Pins
        self.declare_parameter('left_encoder_a', 17)
        self.declare_parameter('left_encoder_b', 27)
        self.declare_parameter('right_encoder_a', 22)
        self.declare_parameter('right_encoder_b', 23)

        # Get parameter values
        self.R = self.get_parameter('wheel_radius').value
        self.L = self.get_parameter('track_width').value
        self.PPR = self.get_parameter('encoder_ppr').value
        self.max_speed = self.get_parameter('max_wheel_speed').value
        self.publish_tf = self.get_parameter('publish_tf').value

        # Encoder state
        self.left_ticks = 0
        self.right_ticks = 0
        self.prev_left_ticks = 0
        self.prev_right_ticks = 0

        # Robot Pose State
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()

        # Target Speeds
        self.target_v = 0.0
        self.target_w = 0.0

        # Hardware Setup
        self.gpio_active = GPIO_AVAILABLE
        if self.gpio_active:
            self.init_gpio()
            self.get_logger().info("Hardware GPIO initialized for L298N & Encoders.")
        else:
            self.get_logger().warn("GPIO library unavailable. Running in Software Simulation Mode.")

        # ROS 2 Interfaces
        self.cmd_vel_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Timer Loop (50 Hz / 20ms update)
        self.timer = self.create_timer(0.02, self.update_loop)

        self.get_logger().info("Motor & Encoder Driver Node running at 50Hz.")

    def init_gpio(self):
        GPIO.setmode(GPIO.BCM)
        
        # Motors setup
        self.left_ena = self.get_parameter('left_motor_ena').value
        self.left_in1 = self.get_parameter('left_motor_in1').value
        self.left_in2 = self.get_parameter('left_motor_in2').value
        self.right_enb = self.get_parameter('right_motor_enb').value
        self.right_in3 = self.get_parameter('right_motor_in3').value
        self.right_in4 = self.get_parameter('right_motor_in4').value

        GPIO.setup([self.left_in1, self.left_in2, self.right_in3, self.right_in4], GPIO.OUT)
        GPIO.setup([self.left_ena, self.right_enb], GPIO.OUT)

        self.pwm_left = GPIO.PWM(self.left_ena, 1000)
        self.pwm_right = GPIO.PWM(self.right_enb, 1000)
        self.pwm_left.start(0)
        self.pwm_right.start(0)

        # Encoders setup
        self.enc_l_a = self.get_parameter('left_encoder_a').value
        self.enc_l_b = self.get_parameter('left_encoder_b').value
        self.enc_r_a = self.get_parameter('right_encoder_a').value
        self.enc_r_b = self.get_parameter('right_encoder_b').value

        GPIO.setup([self.enc_l_a, self.enc_l_b, self.enc_r_a, self.enc_r_b], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(self.enc_l_a, GPIO.RISING, callback=self._left_encoder_cb)
        GPIO.add_event_detect(self.enc_r_a, GPIO.RISING, callback=self._right_encoder_cb)

    def _left_encoder_cb(self, channel):
        if GPIO.input(self.enc_l_b):
            self.left_ticks += 1
        else:
            self.left_ticks -= 1

    def _right_encoder_cb(self, channel):
        if GPIO.input(self.enc_r_b):
            self.right_ticks += 1
        else:
            self.right_ticks -= 1

    def cmd_vel_callback(self, msg: Twist):
        self.target_v = msg.linear.x
        self.target_w = msg.angular.z

    def update_loop(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        # Differential Kinematics: Calculate desired wheel velocities
        # v_R = v + w * (L / 2)
        # v_L = v - w * (L / 2)
        v_r = self.target_v + (self.target_w * self.L / 2.0)
        v_l = self.target_v - (self.target_w * self.L / 2.0)

        # Write to motor drivers
        self.set_motor_speeds(v_l, v_r)

        # Calculate delta distance using hardware encoders or simulation fallback
        if self.gpio_active:
            delta_left_ticks = self.left_ticks - self.prev_left_ticks
            delta_right_ticks = self.right_ticks - self.prev_right_ticks
            self.prev_left_ticks = self.left_ticks
            self.prev_right_ticks = self.right_ticks

            d_left = (2.0 * math.pi * self.R * delta_left_ticks) / self.PPR
            d_right = (2.0 * math.pi * self.R * delta_right_ticks) / self.PPR
        else:
            # Kinematic Simulation Fallback
            d_left = v_l * dt
            d_right = v_r * dt

        d_center = (d_right + d_left) / 2.0
        d_theta = (d_right - d_left) / self.L

        # Update pose integration
        if abs(d_theta) < 1e-6:
            self.x += d_center * math.cos(self.theta)
            self.y += d_center * math.sin(self.theta)
        else:
            radius = d_center / d_theta
            self.x += radius * (math.sin(self.theta + d_theta) - math.sin(self.theta))
            self.y -= radius * (math.cos(self.theta + d_theta) - math.cos(self.theta))

        self.theta += d_theta
        # Normalize theta to [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        v_measured = d_center / dt
        w_measured = d_theta / dt

        # Publish Odometry & TF
        self.publish_odometry(current_time, v_measured, w_measured)
        self.last_time = current_time

    def set_motor_speeds(self, v_l, v_r):
        if not self.gpio_active:
            return

        # Map wheel velocity to PWM duty cycle (0 to 100%)
        duty_l = min(100.0, max(0.0, (abs(v_l) / self.max_speed) * 100.0))
        duty_r = min(100.0, max(0.0, (abs(v_r) / self.max_speed) * 100.0))

        # Left Motor Direction
        if v_l >= 0:
            GPIO.output(self.left_in1, GPIO.HIGH)
            GPIO.output(self.left_in2, GPIO.LOW)
        else:
            GPIO.output(self.left_in1, GPIO.LOW)
            GPIO.output(self.left_in2, GPIO.HIGH)

        # Right Motor Direction
        if v_r >= 0:
            GPIO.output(self.right_in3, GPIO.HIGH)
            GPIO.output(self.right_in4, GPIO.LOW)
        else:
            GPIO.output(self.right_in3, GPIO.LOW)
            GPIO.output(self.right_in4, GPIO.HIGH)

        self.pwm_left.ChangeDutyCycle(duty_l)
        self.pwm_right.ChangeDutyCycle(duty_r)

    def publish_odometry(self, timestamp, v_lin, v_ang):
        q = euler_to_quaternion(0.0, 0.0, self.theta)

        # 1. Publish TF odom -> base_footprint
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = timestamp.to_msg()
            t.header.frame_id = 'odom'
            t.child_frame_id = 'base_footprint'
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation = q
            self.tf_broadcaster.sendTransform(t)

        # 2. Publish Odometry message
        odom = Odometry()
        odom.header.stamp = timestamp.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q

        odom.twist.twist.linear.x = v_lin
        odom.twist.twist.angular.z = v_ang

        self.odom_pub.publish(odom)

    def destroy_node(self):
        if self.gpio_active:
            self.pwm_left.stop()
            self.pwm_right.stop()
            GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorEncoderDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
