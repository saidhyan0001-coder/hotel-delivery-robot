#!/usr/bin/env python3
"""
Interactive 2D Desktop Visualizer for Autonomous Hotel Delivery Robot
Launches a real-time Tkinter GUI window showing top-down floorplan, robot kinematics, LiDAR/Ultrasonic beams, and Vapi AI voice dispatching.
"""

import json
import math
import time
import threading
import tkinter as tk
from tkinter import ttk
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

# Hotel Waypoints: Name -> (x_meters, y_meters, heading_rad)
WAYPOINTS = {
    "Lobby": (1.0, 3.0, 0.0),
    "Room 301": (4.0, 1.2, 0.0),
    "Room 302": (7.0, 1.2, 0.0),
    "Room 303": (10.0, 1.2, 0.0),
    "Room 304": (13.0, 1.2, 0.0),
    "Kitchen": (1.0, 5.0, 1.57),
    "Service Station": (13.0, 5.0, 3.14)
}

# AprilTag Mappings: Room Name -> Tag ID
APRILTAG_MAP = {
    "Lobby": 10,
    "Room 301": 11,
    "Room 302": 12,
    "Room 303": 13,
    "Room 304": 14,
    "Kitchen": 15,
    "Service Station": 16
}


class HotelRobotGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Autonomous Hotel Delivery Robot - Live 2D Visualizer & Nav2 Monitor")
        self.root.geometry("1100x720")
        self.root.configure(bg="#1e1e2e")

        # Robot Physical State (Meters in World Space)
        self.robot_x = 1.0
        self.robot_y = 3.0
        self.robot_theta = 0.0
        self.v_lin = 0.0
        self.v_ang = 0.0

        # Nav2 Navigation State
        self.target_room = "Lobby"
        self.nav_status = "IDLE"
        self.distance_remaining = 0.0
        self.last_detected_tag = 10
        self.speech_text = "System Ready. Standing by at Lobby."

        # Scale Factor: 1 meter = 60 pixels
        self.scale = 55.0
        self.origin_x = 80
        self.origin_y = 60

        self.setup_ui()

        # HTTP Server Thread for Webhooks
        self.server_thread = threading.Thread(target=self.run_http_server, daemon=True)
        self.server_thread.start()

        # Main Animation Loop (50 Hz / 20ms)
        self.update_simulation()

    def world_to_screen(self, wx, wy):
        sx = self.origin_x + wx * self.scale
        sy = self.origin_y + wy * self.scale
        return sx, sy

    def setup_ui(self):
        # Top Header Banner
        header_frame = tk.Frame(self.root, bg="#11111b", height=50)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header_frame,
            text="🤖 AUTONOMOUS HOTEL DELIVERY ROBOT — LIVE 2D SIMULATOR",
            font=("Segoe UI", 14, "bold"),
            fg="#cba6f7",
            bg="#11111b",
            pady=10
        )
        title_label.pack()

        # Main Content Layout: Left Canvas (Visualizer), Right Control Panel
        content_frame = tk.Frame(self.root, bg="#1e1e2e")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. Left Canvas for Top-Down Hotel Map
        canvas_frame = tk.Frame(content_frame, bg="#181825", bd=2, relief=tk.GROOVE)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#181825", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 2. Right Side Control & Telemetry Panel
        panel_frame = tk.Frame(content_frame, bg="#1e1e2e", width=340)
        panel_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Status Box
        status_box = tk.LabelFrame(panel_frame, text=" Robot Telemetry & Status ", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e", pady=5, padx=5)
        status_box.pack(fill=tk.X, pady=(0, 10))

        self.lbl_target = tk.Label(status_box, text="Target Goal: Lobby", font=("Segoe UI", 10), fg="#a6e3a1", bg="#1e1e2e", anchor="w")
        self.lbl_target.pack(fill=tk.X, pady=2)

        self.lbl_status = tk.Label(status_box, text="Nav2 Status: IDLE", font=("Segoe UI", 10, "bold"), fg="#f9e2af", bg="#1e1e2e", anchor="w")
        self.lbl_status.pack(fill=tk.X, pady=2)

        self.lbl_dist = tk.Label(status_box, text="Remaining Dist: 0.00 m", font=("Segoe UI", 10), fg="#cdd6f4", bg="#1e1e2e", anchor="w")
        self.lbl_dist.pack(fill=tk.X, pady=2)

        self.lbl_pos = tk.Label(status_box, text="Pose (x,y,θ): (1.00, 3.00, 0.0°)", font=("Segoe UI", 9), fg="#bac2de", bg="#1e1e2e", anchor="w")
        self.lbl_pos.pack(fill=tk.X, pady=2)

        self.lbl_tag = tk.Label(status_box, text="Ceiling AprilTag: Tag#10 (Lobby)", font=("Segoe UI", 9), fg="#b4befe", bg="#1e1e2e", anchor="w")
        self.lbl_tag.pack(fill=tk.X, pady=2)

        # Speech Box
        speech_box = tk.LabelFrame(panel_frame, text=" Dynamic Voice Output ", font=("Segoe UI", 10, "bold"), fg="#f5c2e7", bg="#1e1e2e", pady=5, padx=5)
        speech_box.pack(fill=tk.X, pady=(0, 10))

        self.lbl_speech = tk.Label(speech_box, text=self.speech_text, font=("Segoe UI", 9, "italic"), fg="#f5e0dc", bg="#1e1e2e", wraplength=300, justify="left")
        self.lbl_speech.pack(fill=tk.X, pady=2)

        # Voice Dispatch Buttons
        dispatch_box = tk.LabelFrame(panel_frame, text=" Voice Dispatch Controls ", font=("Segoe UI", 10, "bold"), fg="#fab387", bg="#1e1e2e", pady=5, padx=5)
        dispatch_box.pack(fill=tk.X, pady=(0, 10))

        btn_r304 = tk.Button(dispatch_box, text="🗣 Vapi AI: Deliver to Room 304", font=("Segoe UI", 9, "bold"), bg="#313244", fg="#a6e3a1", activebackground="#45475a", command=lambda: self.trigger_dispatch("Room 304"))
        btn_r304.pack(fill=tk.X, pady=3)

        btn_r302 = tk.Button(dispatch_box, text="🗣 Offline Prompt: Towel to Room 302", font=("Segoe UI", 9, "bold"), bg="#313244", fg="#89b4fa", activebackground="#45475a", command=lambda: self.trigger_dispatch("Room 302"))
        btn_r302.pack(fill=tk.X, pady=3)

        btn_r301 = tk.Button(dispatch_box, text="🗣 Vapi AI: Deliver to Room 301", font=("Segoe UI", 9), bg="#313244", fg="#cdd6f4", activebackground="#45475a", command=lambda: self.trigger_dispatch("Room 301"))
        btn_r301.pack(fill=tk.X, pady=3)

        btn_lobby = tk.Button(dispatch_box, text="🏠 Return to Lobby Base", font=("Segoe UI", 9), bg="#313244", fg="#f9e2af", activebackground="#45475a", command=lambda: self.trigger_dispatch("Lobby"))
        btn_lobby.pack(fill=tk.X, pady=3)

        # Webhook API Info
        info_box = tk.LabelFrame(panel_frame, text=" Live Webhook API ", font=("Segoe UI", 9, "bold"), fg="#94e2d5", bg="#1e1e2e", pady=5, padx=5)
        info_box.pack(fill=tk.X)

        info_lbl = tk.Label(
            info_box,
            text="HTTP Webhook Active on:\nhttp://localhost:8080/vapi_webhook\nhttp://localhost:8080/voice_prompt",
            font=("Consolas", 8),
            fg="#94e2d5",
            bg="#1e1e2e",
            justify="left"
        )
        info_lbl.pack(fill=tk.X)

    def draw_map(self):
        self.canvas.delete("all")

        # Draw Hotel Corridor Walls
        # Main Corridor
        c_left_x1, c_left_y1 = self.world_to_screen(0.0, 2.0)
        c_left_x2, c_left_y2 = self.world_to_screen(15.0, 2.0)
        self.canvas.create_line(c_left_x1, c_left_y1, c_left_x2, c_left_y2, fill="#585b70", width=4)

        c_right_x1, c_right_y1 = self.world_to_screen(0.0, 4.0)
        c_right_x2, c_right_y2 = self.world_to_screen(15.0, 4.0)
        self.canvas.create_line(c_right_x1, c_right_y1, c_right_x2, c_right_y2, fill="#585b70", width=4)

        # Draw Room Doorways & Labels
        for rname, (wx, wy, _) in WAYPOINTS.items():
            sx, sy = self.world_to_screen(wx, wy)
            tag_id = APRILTAG_MAP.get(rname, 0)

            # Draw Room Box
            rx1, ry1 = sx - 35, sy - 25
            rx2, ry2 = sx + 35, sy + 25

            color = "#a6e3a1" if rname == self.target_room else "#45475a"
            self.canvas.create_rectangle(rx1, ry1, rx2, ry2, outline=color, fill="#313244", width=2)

            # Room Label & AprilTag Indicator
            self.canvas.create_text(sx, sy - 6, text=rname, fill="#cdd6f4", font=("Segoe UI", 9, "bold"))
            self.canvas.create_text(sx, sy + 10, text=f"[Tag #{tag_id}]", fill="#b4befe", font=("Segoe UI", 7))

        # Draw Robot Chassis & Sensors
        rsx, rsy = self.world_to_screen(self.robot_x, self.robot_y)
        body_r = 18

        # 1. LiDAR Scanning Field (Semi-transparent fan arc)
        for i in range(-3, 4):
            angle = self.robot_theta + i * 0.15
            lx = rsx + 45 * math.cos(angle)
            ly = rsy + 45 * math.sin(angle)
            self.canvas.create_line(rsx, rsy, lx, ly, fill="#89b4fa", width=1, dash=(2, 2))

        # 2. Ultrasonic Sensor Rays (3x Front Cones)
        for u_offset in [-0.3, 0.0, 0.3]:
            u_angle = self.robot_theta + u_offset
            ux = rsx + 30 * math.cos(u_angle)
            uy = rsy + 30 * math.sin(u_angle)
            self.canvas.create_line(rsx, rsy, ux, uy, fill="#f9e2af", width=1.5)

        # 3. Main Robot Chassis Box
        self.canvas.create_oval(rsx - body_r, rsy - body_r, rsx + body_r, rsy + body_r, fill="#cba6f7", outline="#f5e0dc", width=2)

        # 4. Heading Indicator Vector
        hx = rsx + 24 * math.cos(self.robot_theta)
        hy = rsy + 24 * math.sin(self.robot_theta)
        self.canvas.create_line(rsx, rsy, hx, hy, fill="#f38ba8", width=3, arrow=tk.LAST)

        # Legend Box
        self.canvas.create_rectangle(10, 10, 240, 60, fill="#11111b", outline="#45475a")
        self.canvas.create_text(125, 22, text="🔵 LiDAR Ray Scanner", fill="#89b4fa", font=("Segoe UI", 8))
        self.canvas.create_text(125, 36, text="🟡 Ultrasonic Sensor Beams", fill="#f9e2af", font=("Segoe UI", 8))
        self.canvas.create_text(125, 48, text="🟣 Robot Footprint (35x35cm)", fill="#cba6f7", font=("Segoe UI", 8))

    def trigger_dispatch(self, room_name):
        self.target_room = room_name
        self.nav_status = "NAVIGATING"
        tx, ty, _ = WAYPOINTS[room_name]
        self.distance_remaining = math.hypot(tx - self.robot_x, ty - self.robot_y)
        self.speech_text = f"Nav2 Goal Accepted: Navigating to {room_name}."
        self.update_telemetry_ui()

    def update_simulation(self):
        if self.nav_status == "NAVIGATING":
            tx, ty, target_yaw = WAYPOINTS[self.target_room]
            dx = tx - self.robot_x
            dy = ty - self.robot_y
            dist = math.hypot(dx, dy)

            if dist > 0.15:
                # Differential Drive Kinematics Integration
                target_heading = math.atan2(dy, dx)
                d_theta = target_heading - self.robot_theta
                d_theta = math.atan2(math.sin(d_theta), math.cos(d_theta))

                # Angular & Linear Speeds
                self.v_ang = max(-1.0, min(1.0, 2.0 * d_theta))
                self.v_lin = max(0.1, min(0.6, 0.8 * dist))

                self.robot_theta += self.v_ang * 0.02
                self.robot_x += self.v_lin * math.cos(self.robot_theta) * 0.02
                self.robot_y += self.v_lin * math.sin(self.robot_theta) * 0.02

                self.distance_remaining = dist
            else:
                self.nav_status = "ARRIVED"
                self.v_lin = 0.0
                self.v_ang = 0.0
                self.distance_remaining = 0.0
                self.last_detected_tag = APRILTAG_MAP.get(self.target_room, 0)
                self.speech_text = f"Ceiling AprilTag Tag#{self.last_detected_tag} verified! I have arrived at {self.target_room}."

            self.update_telemetry_ui()

        self.draw_map()
        self.root.after(20, self.update_simulation)  # 50 Hz refresh

    def update_telemetry_ui(self):
        self.lbl_target.config(text=f"Target Goal: {self.target_room}")
        self.lbl_status.config(text=f"Nav2 Status: {self.nav_status}")
        self.lbl_dist.config(text=f"Remaining Dist: {self.distance_remaining:.2f} m")
        self.lbl_pos.config(text=f"Pose (x,y,θ): ({self.robot_x:.2f}, {self.robot_y:.2f}, {math.degrees(self.robot_theta):.1f}°)")
        self.lbl_tag.config(text=f"Ceiling AprilTag: Tag#{self.last_detected_tag} ({self.target_room})")
        self.lbl_speech.config(text=self.speech_text)

    def run_http_server(self):
        gui_ref = self

        class WebhookHandler(BaseHTTPRequestHandler):

            def _set_headers(self, status=200):
                self.send_response(status)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                payload = json.loads(post_data) if post_data else {}

                room = None
                if self.path == '/vapi_webhook':
                    msg = payload.get('message', {})
                    params = msg.get('parameters', {})
                    room = params.get('room', '')
                elif self.path == '/voice_prompt':
                    text = payload.get('text', '').lower()
                    for r in WAYPOINTS.keys():
                        if r.lower() in text:
                            room = r
                            break

                if room and room in WAYPOINTS:
                    gui_ref.trigger_dispatch(room)
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"status": "SUCCESS", "target": room}).encode('utf-8'))
                else:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"status": "FAILED", "error": "Unknown room"}).encode('utf-8'))

            def log_message(self, format, *args):
                return

        server = HTTPServer(('127.0.0.1', 8080), WebhookHandler)
        server.serve_forever()


def main():
    root = tk.Tk()
    app = HotelRobotGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
