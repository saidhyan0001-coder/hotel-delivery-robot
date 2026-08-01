#!/usr/bin/env python3
"""
MPU6050 IMU Driver Node for Autonomous Hotel Delivery Robot
Interfaces MPU6050 via I2C bus and publishes sensor_msgs/msg/Imu on /imu/data_raw.
"""

import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

SMBUS_AVAILABLE = False
try:
    import smbus2 as smbus
    SMBUS_AVAILABLE = True
except ImportError:
    try:
        import smbus
        SMBUS_AVAILABLE = True
    except ImportError:
        SMBUS_AVAILABLE = False


# MPU6050 Registers
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43


class MPU6050ImuNode(Node):

    def __init__(self):
        super().__init__('mpu6050_imu_node')

        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_address', 0x68)
        self.declare_parameter('frame_id', 'imu_link')
        self.declare_parameter('publish_rate', 50.0)

        self.frame_id = self.get_parameter('frame_id').value
        self.bus_num = self.get_parameter('i2c_bus').value
        self.address = self.get_parameter('i2c_address').value

        self.imu_pub = self.create_publisher(Imu, '/imu/data_raw', 10)

        self.i2c_active = False
        if SMBUS_AVAILABLE:
            try:
                self.bus = smbus.SMBus(self.bus_num)
                # Wake up MPU6050
                self.bus.write_byte_data(self.address, PWR_MGMT_1, 0)
                self.i2c_active = True
                self.get_logger().info(f"MPU6050 initialized on I2C bus {self.bus_num} address {hex(self.address)}")
            except Exception as e:
                self.get_logger().warn(f"Failed to initialize MPU6050 hardware I2C: {e}. Running in Simulation Mode.")
        else:
            self.get_logger().warn("smbus library unavailable. IMU Node running in Simulation Mode.")

        rate = self.get_parameter('publish_rate').value
        self.timer = self.create_timer(1.0 / rate, self.timer_callback)

    def read_word_2c(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg + 1)
        val = (high << 8) + low
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    def timer_callback(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        if self.i2c_active:
            try:
                # Read Raw Acceleration (scale factor 16384 LSB/g)
                ax = self.read_word_2c(ACCEL_XOUT_H) / 16384.0 * 9.80665
                ay = self.read_word_2c(ACCEL_XOUT_H + 2) / 16384.0 * 9.80665
                az = self.read_word_2c(ACCEL_XOUT_H + 4) / 16384.0 * 9.80665

                # Read Raw Gyroscope (scale factor 131 LSB/(deg/s))
                gx = (self.read_word_2c(GYRO_XOUT_H) / 131.0) * (3.14159 / 180.0)
                gy = (self.read_word_2c(GYRO_XOUT_H + 2) / 131.0) * (3.14159 / 180.0)
                gz = (self.read_word_2c(GYRO_XOUT_H + 4) / 131.0) * (3.14159 / 180.0)
            except Exception as e:
                self.get_logger().error(f"I2C read error: {e}")
                ax, ay, az = 0.0, 0.0, 9.80665
                gx, gy, gz = 0.0, 0.0, 0.0
        else:
            # Simulation values (stationary robot)
            ax, ay, az = 0.0, 0.0, 9.80665
            gx, gy, gz = 0.0, 0.0, 0.0

        msg.linear_acceleration.x = float(ax)
        msg.linear_acceleration.y = float(ay)
        msg.linear_acceleration.z = float(az)

        msg.angular_velocity.x = float(gx)
        msg.angular_velocity.y = float(gy)
        msg.angular_velocity.z = float(gz)

        # Identity orientation quaternion
        msg.orientation.w = 1.0
        msg.orientation.x = 0.0
        msg.orientation.y = 0.0
        msg.orientation.z = 0.0

        # Covariance matrices
        msg.orientation_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        msg.angular_velocity_covariance = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
        msg.linear_acceleration_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]

        self.imu_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MPU6050ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
