#!/usr/bin/env python3
"""
Vapi AI Bridge & Local Edge LLM Interface Node for Autonomous Hotel Delivery Robot
Parses dynamic voice intents via Vapi AI Webhook or local TinyLlama fallback, mapping them to Nav2 NavigateToPose actions.
"""

import json
import math
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import String


def euler_to_quaternion(yaw):
    return Quaternion(
        x=0.0,
        y=0.0,
        z=math.sin(yaw / 2.0),
        w=math.cos(yaw / 2.0)
    )


class VapiBridgeHTTPHandler(BaseHTTPRequestHandler):
    node_ref = None  # Reference to VapiRosBridgeNode

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self._set_headers(200)
            status_data = {
                "active_target": self.node_ref.active_target_room,
                "nav_status": self.node_ref.navigation_status,
                "distance_remaining": self.node_ref.distance_remaining
            }
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')

        try:
            payload = json.loads(post_data) if post_data else {}
        except Exception:
            payload = {}

        if self.path == '/vapi_webhook':
            # Handle Primary Vapi AI Webhook Voice Intent Payload
            response_msg = self.node_ref.process_vapi_intent(payload)
            self._set_headers(200)
            self.wfile.write(json.dumps(response_msg).encode('utf-8'))

        elif self.path == '/voice_prompt':
            # Handle Secondary Offline Edge Prompt (TinyLlama / Ollama Fallback)
            text_prompt = payload.get('text', '')
            response_msg = self.node_ref.process_offline_prompt(text_prompt)
            self._set_headers(200)
            self.wfile.write(json.dumps(response_msg).encode('utf-8'))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))

    def log_message(self, format, *args):
        return  # Suppress default HTTP server noise


class VapiRosBridgeNode(Node):

    def __init__(self):
        super().__init__('vapi_ros_bridge_node')

        self.declare_parameter('webhook_port', 8080)
        self.declare_parameter('ollama_url', 'http://localhost:11434/api/generate')
        self.declare_parameter('ollama_model', 'tinyllama')

        self.webhook_port = self.get_parameter('webhook_port').value
        self.ollama_url = self.get_parameter('ollama_url').value
        self.ollama_model = self.get_parameter('ollama_model').value

        # Hotel Room Waypoint Map Database (x, y, yaw)
        self.room_waypoints = {
            "Room 301": (5.0, 1.5, 0.0),
            "Room 302": (10.0, 1.5, 0.0),
            "Room 303": (15.0, 1.5, 0.0),
            "Room 304": (20.0, 1.5, 0.0),
            "Lobby": (0.0, 0.0, 0.0),
            "Kitchen": (-5.0, 2.0, 1.57),
            "Service Station": (-2.0, 0.0, 3.14)
        }

        self.active_target_room = "None"
        self.navigation_status = "IDLE"
        self.distance_remaining = 0.0

        # ROS 2 Action Client for Nav2
        self.nav_action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # TTS / Audio Status Publisher
        self.tts_pub = self.create_publisher(String, '/robot_speech_output', 10)

        # Start HTTP Webhook Server Thread
        VapiBridgeHTTPHandler.node_ref = self
        self.server = HTTPServer(('0.0.0.0', self.webhook_port), VapiBridgeHTTPHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

        self.get_logger().info(f"Vapi AI & LLM ROS Bridge running HTTP Webhook on port {self.webhook_port}.")

    def process_vapi_intent(self, payload):
        """Parse Vapi AI Structured Webhook JSON Payload."""
        self.get_logger().info(f"Received Vapi AI Payload: {payload}")

        # Extract intent and room parameter from nested payload
        message = payload.get('message', {})
        intent = message.get('intent', payload.get('intent', ''))
        params = message.get('parameters', payload.get('parameters', {}))
        room = params.get('room', payload.get('room', ''))

        if not room:
            # Fallback regex extraction from message text
            text = message.get('text', payload.get('transcript', ''))
            room = self.extract_room_from_text(text)

        if room in self.room_waypoints:
            self.send_nav_goal(room)
            response_text = f"Navigating to {room} for delivery."
            self.publish_speech(response_text)
            return {"status": "SUCCESS", "target": room, "message": response_text}
        else:
            response_text = f"Room '{room}' is not in hotel database."
            self.publish_speech(response_text)
            return {"status": "FAILED", "error": response_text}

    def process_offline_prompt(self, text_prompt):
        """Offline Edge Fallback: Uses Local TinyLlama (via Ollama) or Regex Rules."""
        self.get_logger().info(f"Processing offline prompt: '{text_prompt}'")

        # 1. Fast Regex Check
        room = self.extract_room_from_text(text_prompt)

        # 2. If regex fails, query local Ollama TinyLlama REST endpoint
        if not room:
            room = self.query_ollama_tinyllama(text_prompt)

        if room in self.room_waypoints:
            self.send_nav_goal(room)
            response_text = f"Offline Engine: Navigating to {room}."
            self.publish_speech(response_text)
            return {"status": "SUCCESS", "target": room, "message": response_text}
        else:
            response_text = f"Could not determine valid target room from prompt: '{text_prompt}'"
            self.publish_speech("Sorry, I could not recognize the requested destination.")
            return {"status": "FAILED", "error": response_text}

    def extract_room_from_text(self, text):
        text_lower = text.lower()

        for room in self.room_waypoints.keys():
            if room.lower() in text_lower:
                return room

        match = re.search(r'room\s*(\d+)', text_lower)
        if match:
            room_num = match.group(1)
            target = f"Room {room_num}"
            if target in self.room_waypoints:
                return target

        if 'lobby' in text_lower:
            return "Lobby"
        if 'kitchen' in text_lower:
            return "Kitchen"
        if 'service' in text_lower:
            return "Service Station"

        return None

    def query_ollama_tinyllama(self, prompt):
        """Invoke local TinyLlama endpoint to extract room target."""
        system_prompt = f"Available rooms: {list(self.room_waypoints.keys())}. Extract target room from user request as exact name. Output ONLY the room name or 'NONE'."
        data = {
            "model": self.ollama_model,
            "prompt": f"{system_prompt}\nUser request: '{prompt}'\nTarget room:",
            "stream": False
        }
        try:
            req = urllib.request.Request(
                self.ollama_url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=3.0) as response:
                result = json.loads(response.read().decode('utf-8'))
                output_text = result.get('response', '').strip()
                for r in self.room_waypoints.keys():
                    if r.lower() in output_text.lower():
                        return r
        except Exception as e:
            self.get_logger().warn(f"Ollama local LLM query skipped/failed: {e}")

        return None

    def send_nav_goal(self, room_name):
        if not self.nav_action_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("Nav2 NavigateToPose action server unavailable.")
            self.navigation_status = "ACTION_SERVER_UNAVAILABLE"
            return

        x, y, yaw = self.room_waypoints[room_name]
        self.active_target_room = room_name
        self.navigation_status = "NAVIGATING"

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation = euler_to_quaternion(yaw)

        self.get_logger().info(f"Dispatching Nav2 Goal to {room_name}: (x={x}, y={y}, yaw={yaw})")
        send_goal_future = self.nav_action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.nav_feedback_callback
        )
        send_goal_future.add_done_callback(self.nav_goal_response_callback)

    def nav_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Nav2 Goal was rejected by server.")
            self.navigation_status = "GOAL_REJECTED"
            self.publish_speech("Navigation goal was rejected.")
            return

        self.get_logger().info("Nav2 Goal accepted. Executing path...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.nav_result_callback)

    def nav_feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.distance_remaining = feedback.distance_remaining
        self.get_logger().info(f"Nav2 Feedback: {self.distance_remaining:.2f}m remaining to {self.active_target_room}")

    def nav_result_callback(self, future):
        status = future.result().status
        if status == 4:  # STATUS_SUCCEEDED
            self.get_logger().info(f"Successfully arrived at {self.active_target_room}!")
            self.navigation_status = "ARRIVED"
            self.publish_speech(f"I have arrived at {self.active_target_room}. Please collect your item.")
        else:
            self.get_logger().warn(f"Navigation failed with status: {status}")
            self.navigation_status = "FAILED"
            self.publish_speech("Navigation aborted due to unexpected obstacles.")

    def publish_speech(self, text):
        msg = String()
        msg.data = text
        self.tts_pub.publish(msg)

    def destroy_node(self):
        self.server.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VapiRosBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
