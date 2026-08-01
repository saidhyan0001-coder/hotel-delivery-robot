#!/usr/bin/env python3
"""
HC-SR04 Ultrasonic Driver Node for Autonomous Hotel Delivery Robot
Publishes sensor_msgs/msg/Range on Front-Left, Front-Center, and Front-Right topics.
"""

import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range

GPIO_AVAILABLE = False
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False


class UltrasonicDriverNode(Node):

    def __init__(self):
        super().__init__('ultrasonic_driver_node')

        # Declare Sensor Parameters
        self.declare_parameter('min_range', 0.02)     # 2 cm
        self.declare_parameter('max_range', 2.00)     # 2 meters
        self.declare_parameter('field_of_view', 0.26) # ~15 degrees in radians
        self.declare_parameter('publish_rate', 10.0)  # 10 Hz

        # GPIO Pin Definitions (BCM)
        self.declare_parameter('fl_trig_pin', 5)
        self.declare_parameter('fl_echo_pin', 6)
        self.declare_parameter('fc_trig_pin', 13)
        self.declare_parameter('fc_echo_pin', 19)
        self.declare_parameter('fr_trig_pin', 26)
        self.declare_parameter('fr_echo_pin', 21)

        self.min_range = float(self.get_parameter('min_range').value)
        self.max_range = float(self.get_parameter('max_range').value)
        self.fov = float(self.get_parameter('field_of_view').value)

        # Topic Publishers
        self.pub_fl = self.create_publisher(Range, '/ultrasonic/front_left', 10)
        self.pub_fc = self.create_publisher(Range, '/ultrasonic/front_center', 10)
        self.pub_fr = self.create_publisher(Range, '/ultrasonic/front_right', 10)

        # Hardware Setup
        self.gpio_active = GPIO_AVAILABLE
        if self.gpio_active:
            self.init_gpio()
            self.get_logger().info("Hardware GPIO initialized for 3x HC-SR04 sensors.")
        else:
            self.get_logger().warn("GPIO library unavailable. Ultrasonic Node running in Simulation Mode.")

        rate = self.get_parameter('publish_rate').value
        self.timer = self.create_timer(1.0 / rate, self.timer_callback)

    def init_gpio(self):
        GPIO.setmode(GPIO.BCM)
        self.sensors = {
            'fl': (self.get_parameter('fl_trig_pin').value, self.get_parameter('fl_echo_pin').value),
            'fc': (self.get_parameter('fc_trig_pin').value, self.get_parameter('fc_echo_pin').value),
            'fr': (self.get_parameter('fr_trig_pin').value, self.get_parameter('fr_echo_pin').value)
        }
        for name, (trig, echo) in self.sensors.items():
            GPIO.setup(trig, GPIO.OUT)
            GPIO.setup(echo, GPIO.IN)
            GPIO.output(trig, GPIO.LOW)
        time.sleep(0.1)

    def measure_distance(self, trig, echo):
        if not self.gpio_active:
            return self.max_range  # Simulation fallback

        # Send 10us trigger pulse
        GPIO.output(trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(trig, GPIO.LOW)

        start_time = time.time()
        stop_time = time.time()
        timeout = start_time + 0.03  # 30ms timeout (~5m max range)

        while GPIO.input(echo) == 0:
            start_time = time.time()
            if start_time > timeout:
                return self.max_range

        while GPIO.input(echo) == 1:
            stop_time = time.time()
            if stop_time > timeout:
                return self.max_range

        elapsed = stop_time - start_time
        distance = (elapsed * 343.0) / 2.0  # speed of sound = 343 m/s
        return max(self.min_range, min(self.max_range, distance))

    def create_range_msg(self, frame_id, distance):
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.radiation_type = Range.ULTRASOUND
        msg.field_of_view = self.fov
        msg.min_range = self.min_range
        msg.max_range = self.max_range
        msg.range = float(distance)
        return msg

    def timer_callback(self):
        if self.gpio_active:
            d_fl = self.measure_distance(*self.sensors['fl'])
            d_fc = self.measure_distance(*self.sensors['fc'])
            d_fr = self.measure_distance(*self.sensors['fr'])
        else:
            d_fl = self.max_range
            d_fc = self.max_range
            d_fr = self.max_range

        self.pub_fl.publish(self.create_range_msg('ultrasonic_fl_link', d_fl))
        self.pub_fc.publish(self.create_range_msg('ultrasonic_fc_link', d_fc))
        self.pub_fr.publish(self.create_range_msg('ultrasonic_fr_link', d_fr))

    def destroy_node(self):
        if self.gpio_active:
            GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
