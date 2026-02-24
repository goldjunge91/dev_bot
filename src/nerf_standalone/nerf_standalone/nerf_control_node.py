#!/usr/bin/env python3
"""
Nerf Control Node - High-Level Launcher Control
================================================
Bietet High-Level ROS2 Interface für Nerf Launcher

Services:
- /nerf/fire (Trigger) - Führt komplette Schuss-Sequenz aus

Topics (Subscribed):
- /nerf/tilt (Float64MultiArray) - Normalisierte Tilt-Position [0.0-1.0]
  * 0.0 = Unten (5.23 rad ≈ 300°)
  * 0.5 = Horizontal (5.75 rad)
  * 1.0 = Oben (6.28 rad ≈ 360°)

Topics (Published):
- /trigger_controller/commands - Tilt Servo Position (Radiant)
- /flywheel_controller/commands - Flywheel Motor Geschwindigkeiten
- /pusher_controller/commands - Pusher Servo Geschwindigkeit

Schuss-Sequenz:
1. Flywheels hochfahren (1s)
2. Pusher vorwärts (0.5s)
3. Pusher stoppen
4. Flywheels stoppen
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger
import time


class NerfControlNode(Node):
    def __init__(self):
        super().__init__("nerf_control_node")

        # Publishers: Steuern Hardware-Controller
        # Queue Size 10 = Puffert max. 10 Befehle, alte werden verworfen
        self.trigger_pub = self.create_publisher(
            Float64MultiArray,
            "/trigger_controller/commands",
            10,  # Tilt Servo
        )
        self.flywheel_pub = self.create_publisher(
            Float64MultiArray,
            "/flywheel_controller/commands",
            10,  # Flywheel Motoren
        )
        self.pusher_pub = self.create_publisher(
            Float64MultiArray,
            "/pusher_controller/commands",
            10,  # Pusher Servo
        )

        # Subscribers: Empfängt Tilt-Befehle
        # Queue Size 10 = Puffert eingehende Nachrichten
        self.create_subscription(
            Float64MultiArray, "/nerf/tilt", self.tilt_callback, 10
        )

        # Services: Bietet Fire-Service an
        self.create_service(Trigger, "/nerf/fire", self.fire_callback)

        # Parameters: Physikalische Grenzen
        self.tilt_min = 5.23  # ~300° (Unten)
        self.tilt_max = 6.28  # ~360° (Oben)

        self.get_logger().info("Nerf Control Node Started")

        # Initialisierungs-Timer (einmalig nach 1s)
        # HINWEIS: Kann gelöscht werden wenn nicht benötigt
        self.init_timer = self.create_timer(1.0, self.init_callback)

    def init_callback(self):
        """
        Initialisiert Launcher-Position auf 'UP' (6.28 rad)
        Läuft nur einmal
        """
        self.get_logger().info("Initializing Launcher Position to UP (6.28)...")
        cmd = Float64MultiArray()
        cmd.data = [6.28]
        self.trigger_pub.publish(cmd)

        # Timer zerstören damit er nur einmal läuft
        self.init_timer.cancel()
        self.get_logger().info("Initialization Complete.")

    def tilt_callback(self, msg):
        """
        Akzeptiert normalisierte Tilt-Werte [0.0 - 1.0]

        Mapping:
        0.0 = Unten (5.23 rad ≈ 300°)
        0.5 = Horizontal (5.75 rad)
        1.0 = Oben (6.28 rad ≈ 360°)

        Beispiel:
        - msg.data = [0.0] → Launcher zeigt nach unten
        - msg.data = [1.0] → Launcher zeigt nach oben
        """
        # Nimm erstes Element falls Array
        if len(msg.data) > 0:
            target_norm = msg.data[0]

            # Begrenze Eingabe auf 0-1
            target_norm = max(0.0, min(1.0, target_norm))

            # Mappe auf physikalische Winkel
            target_phys = self.tilt_min + (
                target_norm * (self.tilt_max - self.tilt_min)
            )

            # Publiziere sicher
            cmd = Float64MultiArray()
            cmd.data = [target_phys]
            self.trigger_pub.publish(cmd)
            self.get_logger().debug(
                f"Tilt Command: {target_norm} -> Physical: {target_phys:.2f}"
            )

    def fire_callback(self, request, response):
        """
        Service Callback: Führt komplette Schuss-Sequenz aus

        Sequenz:
        1. Flywheels auf 100% hochfahren
        2. 1 Sekunde warten für Spin-Up
        3. Pusher vorwärts mit 10.0 Geschwindigkeit
        4. 0.5 Sekunden warten
        5. Pusher stoppen (0.0)
        6. Flywheels stoppen

        HINWEIS: time.sleep() blockiert Node!
        Für Produktion: Verwende Timer oder Action Server
        """
        self.get_logger().info("FIRE SEQUENCE INITIATED")

        # 1. Flywheels hochfahren
        cmd_fly = Float64MultiArray()
        cmd_fly.data = [100.0, 100.0]  # Beide Motoren 100%
        self.flywheel_pub.publish(cmd_fly)
        self.get_logger().info("Flywheels SPINNING UP...")
        time.sleep(1.0)  # Warte auf Spin-Up

        # 2. Dart schieben
        cmd_push = Float64MultiArray()
        cmd_push.data = [10.0]  # Geschwindigkeit
        self.pusher_pub.publish(cmd_push)
        self.get_logger().info("Pusher ADVANCE")
        time.sleep(0.5)  # Warte auf Push

        # 3. Pusher zurückziehen (Stoppen/Rückwärts?)
        # Für Continuous Servo: 0.0 = Stopp
        cmd_push.data = [0.0]
        self.pusher_pub.publish(cmd_push)
        self.get_logger().info("Pusher STOP")

        # 4. Flywheels herunterfahren
        cmd_fly.data = [0.0, 0.0]
        self.flywheel_pub.publish(cmd_fly)
        self.get_logger().info("Flywheels STOP")

        response.success = True
        response.message = "Dart fired!"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = NerfControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
