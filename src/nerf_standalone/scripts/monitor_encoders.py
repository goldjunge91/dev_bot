#!/usr/bin/env python3
"""
Encoder Monitor - Echtzeit Encoder-Positions-Anzeige
====================================================
Zeigt kontinuierlich die Encoder-Positionen der Räder an
Continuously displays wheel encoder positions

Verwendung / Usage:
  ros2 run nerf_standalone monitor_encoders.py

Ausgabe / Output:
  Left: 1.2345  |  Right: 2.3456
  
Nützlich für / Useful for:
- Debugging Encoder-Verbindungen / Debugging encoder connections
- Überprüfung Encoder-Richtung / Checking encoder direction
- Kalibrierung / Calibration
- Echtzeit-Feedback während Tests / Real-time feedback during tests

CTRL-C zum Beenden / CTRL-C to exit
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class EncoderMonitor(Node):
    def __init__(self):
        super().__init__("encoder_monitor")
        # Subscriber: Empfängt Joint States (enthält Encoder-Daten)
        # Subscriber: Receives joint states (contains encoder data)
        self.subscription = self.create_subscription(
            JointState, "/joint_states", self.listener_callback, 10
        )
        self.get_logger().info("Monitoring Encoder Positions...")
        self.get_logger().info("-------------------------------")

    def listener_callback(self, msg):
        """
        Callback: Zeigt Encoder-Positionen in Echtzeit
        Callback: Displays encoder positions in real-time
        
        Verwendet Carriage Return (\r) für Überschreiben der Zeile
        Uses carriage return (\r) to overwrite the line
        """
        # Erstelle Dictionary für einfachen Zugriff
        # Create dictionary for easy lookup
        positions = {}
        for name, pos in zip(msg.name, msg.position):
            positions[name] = pos

        # Hole Rad-Positionen (Standard: None falls nicht gefunden)
        # Get wheel positions (default to None if not found)
        left = positions.get("left_wheel_joint")
        right = positions.get("right_wheel_joint")

        if left is not None and right is not None:
            # Formatierte Ausgabe mit Überschreiben (Carriage Return)
            # Formatted output with overwrite (carriage return)
            # \r = Zurück zum Zeilenanfang / Return to line start
            # end="" = Kein Zeilenumbruch / No newline
            # flush=True = Sofort ausgeben / Output immediately
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
