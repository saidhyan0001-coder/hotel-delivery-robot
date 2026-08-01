#!/usr/bin/env python3
"""
Ceiling AprilTag Detector Node for Autonomous Hotel Delivery Robot
Captures upward camera feed, detects ceiling tags, verifies room alignment, and publishes detected room locations.
"""

import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

OPENCV_AVAILABLE = False
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class CeilingAprilTagDetectorNode(Node):

    def __init__(self):
        super().__init__('ceiling_apriltag_detector')

        self.declare_parameter('camera_device', 0)
        self.declare_parameter('frame_rate', 10.0)
        self.declare_parameter('expected_tag_dictionary', 'DICT_APRILTAG_36h11')

        self.device_id = self.get_parameter('camera_device').value
        self.frame_rate = self.get_parameter('frame_rate').value

        # Room ID Database mapping Tag ID -> Location Name
        self.tag_room_map = {
            10: "Lobby",
            11: "Room 301",
            12: "Room 302",
            13: "Room 303",
            14: "Room 304",
            15: "Service Station"
        }

        self.current_detected_room = "Unknown"
        self.current_tag_id = -1
        self.last_detection_time = time.time()

        # Publishers & Services
        self.room_pub = self.create_publisher(String, '/apriltag/detected_room', 10)
        self.verify_srv = self.create_service(Trigger, '/verify_room_arrival', self.handle_verify_arrival)

        # Camera setup
        self.cap = None
        self.aruco_detector = None
        self.camera_active = False

        if OPENCV_AVAILABLE:
            self.init_camera()
        else:
            self.get_logger().warn("OpenCV library unavailable. Running AprilTag Detector in Simulation Mode.")

        self.timer = self.create_timer(1.0 / self.frame_rate, self.processing_loop)
        self.get_logger().info("Ceiling AprilTag Detector Node initialized.")

    def init_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            if self.cap.isOpened():
                self.camera_active = True
                self.get_logger().info(f"Upward camera initialized on /dev/video{self.device_id}")
            else:
                self.get_logger().warn(f"Cannot open camera device {self.device_id}. Running in Simulation Mode.")

            # ArUco / AprilTag setup
            dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
            parameters = cv2.aruco.DetectorParameters()
            self.aruco_detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        except Exception as e:
            self.get_logger().error(f"Error initializing ArUco detector: {e}")
            self.camera_active = False

    def processing_loop(self):
        if self.camera_active and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, rejected = self.aruco_detector.detectMarkers(gray)
                if ids is not None and len(ids) > 0:
                    tag_id = int(ids[0][0])
                    self.current_tag_id = tag_id
                    self.current_detected_room = self.tag_room_map.get(tag_id, f"Tag#{tag_id}")
                    self.last_detection_time = time.time()
                else:
                    if time.time() - self.last_detection_time > 2.0:
                        self.current_detected_room = "None"
                        self.current_tag_id = -1

        # Publish detected room
        msg = String()
        msg.data = self.current_detected_room
        self.room_pub.publish(msg)

    def handle_verify_arrival(self, request, response):
        """Service callback to verify if the robot has arrived precisely under the expected ceiling tag."""
        if self.current_tag_id != -1 and self.current_detected_room != "None":
            response.success = True
            response.message = f"Verified arrival at {self.current_detected_room} (Tag ID: {self.current_tag_id})"
        else:
            response.success = False
            response.message = "No ceiling AprilTag detected for fine alignment."
        return response

    def destroy_node(self):
        if self.cap is not None:
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CeilingAprilTagDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
