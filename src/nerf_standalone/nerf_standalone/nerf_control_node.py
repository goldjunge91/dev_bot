#!/usr/bin/env python3
"""
Nerf Control Node - High-Level Launcher Control
================================================
Bietet High-Level ROS2 Interface für Nerf Launcher
Provides high-level ROS2 interface for Nerf launcher

Services:
- /nerf/fire (Trigger) - Führt komplette Schuss-Sequenz aus / Executes complete fire sequence

Topics (Subscribed):
- /nerf/tilt (Float64MultiArray) - Normalisierte Tilt-Position [0.0-1.0]
  * 0.0 = Unten/Bottom (5.23 rad ≈ 300°)
  * 0.5 = Horizontal (5.75 rad)
  * 1.0 = Oben/Top (6.28 rad ≈ 360°)

Topics (Published):
- /trigger_controller/commands - Tilt Servo Position (Radiant)
- /flywheel_controller/commands - Flywheel Motor Geschwindigkeiten
- /pusher_controller/commands - Pusher Servo Geschwindigkeit

Schuss-Sequenz / Fire Sequence:
1. Flywheels hochfahren (1s) / Spin up flywheels (1s)
2. Pusher vorwärts (0.5s) / Push dart forward (0.5s)
3. Pusher stoppen / Stop pusher
4. Flywheels stoppen / Stop flywheels
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger
import time


class NerfControlNode(Node):
    def __init__(self):
        super().__init__("nerf_control_node")

        # Publishers: Steuern Hardware-Controller / Control hardware controllers
        # Queue Size 10 = Puffert max. 10 Befehle, alte werden verworfen
        # Queue Size 10 = Buffers max 10 commands, old ones are discarded
        self.trigger_pub = self.create_publisher(
            Float64MultiArray, "/trigger_controller/commands", 10  # Tilt Servo
        )
        self.flywheel_pub = self.create_publisher(
            Float64MultiArray, "/flywheel_controller/commands", 10  # Flywheel Motoren
        )
        self.pusher_pub = self.create_publisher(
            Float64MultiArray, "/pusher_controller/commands", 10  # Pusher Servo
        )

        # Subscribers: Empfängt Tilt-Befehle / Receives tilt commands
        # Queue Size 10 = Puffert eingehende Nachrichten / Buffers incoming messages
        self.create_subscription(
            Float64MultiArray, "/nerf/tilt", self.tilt_callback, 10
        )

        # Services: Bietet Fire-Service an / Provides fire service
        self.create_service(Trigger, "/nerf/fire", self.fire_callback)

        # Parameters: Physikalische Grenzen / Physical limits
        self.tilt_min = 5.23  # ~300° (Unten/Down)
        self.tilt_max = 6.28  # ~360° (Oben/Up)

        self.get_logger().info("Nerf Control Node Started")
        
        # Initialisierungs-Timer (einmalig nach 1s)
        # Initialization timer (once after 1s)
        # HINWEIS: Kann gelöscht werden wenn nicht benötigt
        # NOTE: Can be deleted if not needed
        self.init_timer = self.create_timer(1.0, self.init_callback)

    def init_callback(self):
        """
        Initialisiert Launcher-Position auf 'UP' (6.28 rad)
        Initializes launcher position to 'UP' (6.28 rad)
        Läuft nur einmal / Runs only once
        """
        self.get_logger().info("Initializing Launcher Position to UP (6.28)...")
        cmd = Float64MultiArray()
        cmd.data = [6.28]
        self.trigger_pub.publish(cmd)

        # Timer zerstören damit er nur einmal läuft
        # Destroy timer so it only runs once
        self.init_timer.cancel()
        self.get_logger().info("Initialization Complete.")

    def tilt_callback(self, msg):
        """
        Akzeptiert normalisierte Tilt-Werte [0.0 - 1.0]
        Accepts normalized tilt values [0.0 - 1.0]
        
        Mapping:
        0.0 = Unten/Bottom (5.23 rad ≈ 300°)
        0.5 = Horizontal (5.75 rad)
        1.0 = Oben/Top (6.28 rad ≈ 360°)
        
        Beispiel / Example:
        - msg.data = [0.0] → Launcher zeigt nach unten / points down
        - msg.data = [1.0] → Launcher zeigt nach oben / points up
        """
        # Nimm erstes Element falls Array / Take first element if array
        if len(msg.data) > 0:
            target_norm = msg.data[0]

            # Begrenze Eingabe auf 0-1 / Clamp input to 0-1
            target_norm = max(0.0, min(1.0, target_norm))

            # Mappe auf physikalische Winkel / Map to physical angles
            target_phys = self.tilt_min + (
                target_norm * (self.tilt_max - self.tilt_min)
            )

            # Publiziere sicher / Publish safely
            cmd = Float64MultiArray()
            cmd.data = [target_phys]
            self.trigger_pub.publish(cmd)
            self.get_logger().info(
                f"Tilt Command: {target_norm} -> Physical: {target_phys:.2f}"
            )

    def fire_callback(self, request, response):
        """
        Service Callback: Führt komplette Schuss-Sequenz aus
        Service callback: Executes complete fire sequence
        
        Sequenz / Sequence:
        1. Flywheels auf 100% hochfahren / Spin up flywheels to 100%
        2. 1 Sekunde warten für Spin-Up / Wait 1 second for spin-up
        3. Pusher vorwärts mit 10.0 Geschwindigkeit / Push dart forward at 10.0 speed
        4. 0.5 Sekunden warten / Wait 0.5 seconds
        5. Pusher stoppen (0.0) / Stop pusher (0.0)
        6. Flywheels stoppen / Stop flywheels
        
        HINWEIS: time.sleep() blockiert Node!
        NOTE: time.sleep() blocks the node!
        Für Produktion: Verwende Timer oder Action Server
        For production: Use timers or action server
        """
        self.get_logger().info("FIRE SEQUENCE INITIATED")

        # 1. Flywheels hochfahren / Spin up flywheels
        cmd_fly = Float64MultiArray()
        cmd_fly.data = [100.0, 100.0]  # Beide Motoren 100% / Both motors 100%
        self.flywheel_pub.publish(cmd_fly)
        self.get_logger().info("Flywheels SPINNING UP...")
        time.sleep(1.0)  # Warte auf Spin-Up / Wait for spin up

        # 2. Dart schieben / Push dart
        cmd_push = Float64MultiArray()
        cmd_push.data = [10.0]  # Geschwindigkeit / Velocity
        self.pusher_pub.publish(cmd_push)
        self.get_logger().info("Pusher ADVANCE")
        time.sleep(0.5)  # Warte auf Push / Wait for push

        # 3. Pusher zurückziehen (Stoppen/Rückwärts?)
        # 3. Retract pusher (Stop/Reverse?)
        # Für Continuous Servo: 0.0 = Stopp / For continuous servo: 0.0 = stop
        cmd_push.data = [0.0]
        self.pusher_pub.publish(cmd_push)
        self.get_logger().info("Pusher STOP")

        # 4. Flywheels herunterfahren / Spin down flywheels
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
