#!/usr/bin/env python3

# Copyright 2026 Developer
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
"""
Encoder Monitor - Echtzeit Encoder-Positions-Anzeige.

====================================================
Zeigt kontinuierlich die Encoder-Positionen der Räder an

Verwendung:
  ros2 run nerf_launch_system monitor_encoders.py

Ausgabe:
  Left: 1.2345  |  Right: 2.3456

Nützlich für:
- Debugging Encoder-Verbindungen
- Überprüfung Encoder-Richtung
- Kalibrierung
- Echtzeit-Feedback während Tests

CTRL-C zum Beenden
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class EncoderMonitor(Node):
    def __init__(self):
        super().__init__("encoder_monitor")
        # Subscriber: Empfängt Joint States (enthält Encoder-Daten)
        self.subscription = self.create_subscription(
            JointState, "/joint_states", self.listener_callback, 10
        )
        self.get_logger().info("Monitoring Encoder Positions...")
        self.get_logger().info("-------------------------------")

    def listener_callback(self, msg):
        r"""
        Zeigt Encoder-Positionen in Echtzeit.

        Verwendet Carriage Return (\r) für Überschreiben der Zeile.
        """
        # Erstelle Dictionary für einfachen Zugriff
        positions = {}
        for name, pos in zip(msg.name, msg.position):
            positions[name] = pos

        # Hole Rad-Positionen (Standard: None falls nicht gefunden)
        left = positions.get("left_wheel_joint")
        right = positions.get("right_wheel_joint")

        if left is not None and right is not None:
            # Formatierte Ausgabe mit Überschreiben (Carriage Return)
            # \r = Zurück zum Zeilenanfang
            # end="" = Kein Zeilenumbruch
            # flush=True = Sofort ausgeben
            print(f"\rLeft: {left:10.4f}  |  Right: {right:10.4f}", end="", flush=True)


def main(args=None):
    rclpy.init(args=args)
    encoder_monitor = EncoderMonitor()
    try:
        rclpy.spin(encoder_monitor)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nMonitor stopped.")
        encoder_monitor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
