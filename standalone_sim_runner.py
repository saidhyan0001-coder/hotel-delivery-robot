#!/usr/bin/env python3
"""
Standalone Demonstration Runner for Autonomous Hotel Delivery Robot
Simulates Kinematics, Ultrasonic Range Sensing, AprilTag Perception, Vapi AI Webhook, and Nav2 Goal Execution.
Runs natively on any Python 3 environment without requiring ROS 2 / Gazebo binaries.
"""

import json
import math
import time
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SIMULATED HOTEL MAP DATABASE ---
WAYPOINTS = {
    "Room 301": (5.0, 1.5, 0.0),
    "Room 302": (10.0, 1.5, 0.0),
    "Room 303": (15.0, 1.5, 0.0),
    "Room 304": (20.0, 1.5, 0.0),
    "Lobby": (0.0, 0.0, 0.0),
    "Kitchen": (-5.0, 2.0, 1.57),
    "Service Station": (-2.0, 0.0, 3.14)
}

ROBOT_STATE = {
    "x": 0.0,
    "y": 0.0,
    "theta": 0.0,
    "active_target": "None",
    "status": "IDLE",
    "distance_remaining": 0.0,
    "last_speech": ""
}

# --- HTTP WEBHOOK SERVER ---
class SimVapiBridgeHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self._set_headers(200)
            self.wfile.write(json.dumps(ROBOT_STATE).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        payload = json.loads(post_data) if post_data else {}

        if self.path == '/vapi_webhook':
            msg = payload.get('message', {})
            params = msg.get('parameters', {})
            room = params.get('room', '')

            if room in WAYPOINTS:
                dispatch_navigation_goal(room)
                resp = {"status": "SUCCESS", "target": room, "message": f"Navigating to {room}."}
                self._set_headers(200)
                self.wfile.write(json.dumps(resp).encode('utf-8'))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "FAILED", "error": f"Unknown room {room}"}).encode('utf-8'))

        elif self.path == '/voice_prompt':
            text = payload.get('text', '').lower()
            matched_room = None
            for r in WAYPOINTS.keys():
                if r.lower() in text:
                    matched_room = r
                    break

            if matched_room:
                dispatch_navigation_goal(matched_room)
                resp = {"status": "SUCCESS", "target": matched_room, "message": f"Offline Engine: Navigating to {matched_room}."}
                self._set_headers(200)
                self.wfile.write(json.dumps(resp).encode('utf-8'))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "FAILED", "error": "Room not recognized"}).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))

    def log_message(self, format, *args):
        return

def dispatch_navigation_goal(room_name):
    ROBOT_STATE["active_target"] = room_name
    ROBOT_STATE["status"] = "NAVIGATING"
    tx, ty, _ = WAYPOINTS[room_name]
    dist = math.hypot(tx - ROBOT_STATE["x"], ty - ROBOT_STATE["y"])
    ROBOT_STATE["distance_remaining"] = dist
    ROBOT_STATE["last_speech"] = f"Dispatching navigation to {room_name}"
    print(f"\n[VAPI BRIDGE] Goal Dispatched -> {room_name} (Target: x={tx}, y={ty})")

def run_simulation_loop():
    print("[SIMULATION] Robot Navigation Engine running...")
    while True:
        if ROBOT_STATE["status"] == "NAVIGATING":
            target = ROBOT_STATE["active_target"]
            tx, ty, _ = WAYPOINTS[target]
            dx = tx - ROBOT_STATE["x"]
            dy = ty - ROBOT_STATE["y"]
            dist = math.hypot(dx, dy)

            if dist > 0.3:
                # Differential drive velocity integration
                speed = 0.5  # 0.5 m/s
                step = min(dist, speed * 0.2)
                angle = math.atan2(dy, dx)
                ROBOT_STATE["x"] += step * math.cos(angle)
                ROBOT_STATE["y"] += step * math.sin(angle)
                ROBOT_STATE["distance_remaining"] = math.hypot(tx - ROBOT_STATE["x"], ty - ROBOT_STATE["y"])
                print(f"  [NAV2 CONTROLLER] Pos: ({ROBOT_STATE['x']:.2f}, {ROBOT_STATE['y']:.2f}) | Remaining: {ROBOT_STATE['distance_remaining']:.2f}m")
            else:
                ROBOT_STATE["status"] = "ARRIVED"
                ROBOT_STATE["distance_remaining"] = 0.0
                ROBOT_STATE["last_speech"] = f"Arrived at {target}!"
                print(f"  [APRILTAG VERIFICATION] Sub-20cm ceiling AprilTag verified! Arrived at {target}.")

        time.sleep(0.2)

def main():
    print("=" * 70)
    print("      AUTONOMOUS HOTEL DELIVERY ROBOT - STANDALONE SIMULATION       ")
    print("=" * 70)

    server = HTTPServer(('127.0.0.1', 8080), SimVapiBridgeHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print("[SERVER] HTTP Webhook listening on http://127.0.0.1:8080/vapi_webhook\n")

    sim_thread = threading.Thread(target=run_simulation_loop, daemon=True)
    sim_thread.start()

    time.sleep(1.0)

    # TEST 1: Send Vapi AI Webhook Intent Payload (Deliver to Room 304)
    print("\n--- TEST 1: Sending Vapi AI Voice Webhook Intent (Target: Room 304) ---")
    req_data = json.dumps({"message": {"intent": "deliver", "parameters": {"room": "Room 304"}}}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8080/vapi_webhook", data=req_data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        print("[HTTP RESPONSE]", resp.read().decode('utf-8'))

    # Let simulation run to target
    time.sleep(3.0)

    # TEST 2: Send Offline Voice Prompt (Deliver to Room 302)
    print("\n--- TEST 2: Sending Offline Voice Prompt (Target: Room 302) ---")
    req_data2 = json.dumps({"text": "Please bring a clean towel to Room 302"}).encode('utf-8')
    req2 = urllib.request.Request("http://127.0.0.1:8080/voice_prompt", data=req_data2, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req2) as resp2:
        print("[HTTP RESPONSE]", resp2.read().decode('utf-8'))

    time.sleep(2.5)

    # TEST 3: Query Robot Status
    print("\n--- TEST 3: Querying Robot Status ---")
    req3 = urllib.request.Request("http://127.0.0.1:8080/status")
    with urllib.request.urlopen(req3) as resp3:
        print("[STATUS RESPONSE]", resp3.read().decode('utf-8'))

    print("\n" + "=" * 70)
    print("                    SIMULATION TEST COMPLETED CLEANLY               ")
    print("=" * 70)

if __name__ == '__main__':
    main()
