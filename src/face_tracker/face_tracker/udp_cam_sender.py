# Copyright 2026 goldjunge91
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket

import cv2
import rclpy
from rclpy.node import Node

"""
Zweck dieses Nodes (Offloading):
Die Gesichtserkennung benötigt viel Rechenleistung. Wenn sie direkt auf dem Raspberry Pi
ausgeführt wird, sinkt die Bildrate (FPS) stark ab und die CPU überhitzt.

Dieser Node dient als 'Auge' am Roboter:
1. Er fängt das Kamerabild am Roboter ein.
2. Er komprimiert es als JPEG und schickt es via UDP an einen starken PC.
3. Der PC übernimmt die schwere Arbeit (Erkennung) und schickt Steuerbefehle zurück.
"""


class UdpCamSender(Node):
    def __init__(self):
        super().__init__("udp_cam_sender")

        # Parameter
        self.declare_parameter("target_ip", "127.0.0.1")
        self.declare_parameter("port", 9999)
        self.declare_parameter("camera_index", 0)
        self.declare_parameter("fps_limit", 30)

        self.target_ip = self.get_parameter("target_ip").value
        self.port = self.get_parameter("port").value
        self.camera_index = self.get_parameter("camera_index").value
        self.fps_limit = self.get_parameter("fps_limit").value

        # UDP Socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000)

        # Kamera initialisieren
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        if not self.cap.isOpened():
            self.get_logger().error(f"Kamera {self.camera_index} konnte nicht geöffnet werden!")
            return

        self.get_logger().info(
            f"Starte Stream an {self.target_ip}:{self.port} (FPS Limit: {self.fps_limit})"
        )

        # Timer für Stream (ca. 30 FPS)
        timer_period = 1.0 / self.fps_limit
        self.timer = self.create_timer(timer_period, self.send_frame)

    def send_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Frame als JPEG komprimieren (Qualität 80)
        _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        # Daten senden
        try:
            self.client_socket.sendto(buffer.tobytes(), (self.target_ip, self.port))
        except Exception as e:
            self.get_logger().warn(f"Sende-Fehler: {e}")

    def destroy_node(self):
        self.cap.release()
        self.client_socket.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UdpCamSender()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
