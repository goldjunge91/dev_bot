#!/usr/bin/env python3
"""
Nerf Control Node - High-Level Launcher Control
================================================
Bietet High-Level ROS2 Interface für Nerf Launcher

Services:
- /nerf/fire (Trigger) - Führt komplette Schuss-Sequenz aus

Topics (Subscribed):
- /nerf/tilt (Float64MultiArray) - Normalisierte Tilt-Position [0.0-1.0]
  * 0.0 = Unten (-0.52 rad, Joint-Space)
  * 0.5 = Horizontal (0.0 rad)
  * 1.0 = Oben (+0.52 rad)
  # ALT: Servo-Rohwerte 5.23–6.28 rad — kollidierte mit den URDF-Limits
  #      (±0.52) in der Simulation; NerfSystem arbeitet jetzt in Joint-Space

Topics (Published):
- /trigger_controller/commands - Tilt Servo Position (Radiant)
# - /flywheel_controller/commands - Flywheel Motor Geschwindigkeiten (entfernt: Firmware-FSM steuert autonom)
- /pusher_controller/commands - Pusher Servo Geschwindigkeit

Schuss-Sequenz:
    Die komplette Sequenz wird an die Firmware-FSM delegiert.
    Der ROS2-Node sendet nur den SHOT-Befehl über den Pusher-Controller.
    Die FSM steuert autonom: SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger
# import time  # Entfernt: FSM übernimmt Timing, kein sleep() nötig


class NerfControlNode(Node):
    def __init__(self):
        super().__init__("nerf_control_node")

        self.declare_parameter("auto_arm", False)
        self.auto_arm = self.get_parameter("auto_arm").value

        # Publishers: Steuern Hardware-Controller
        # Queue Size 10 = Puffert max. 10 Befehle, alte werden verworfen
        self.trigger_pub = self.create_publisher(
            Float64MultiArray,
            "/trigger_controller/commands",
            10,  # Tilt Servo
        )
        # Hinweis: flywheel_pub entfernt – die Firmware-FSM steuert die
        # Flywheels autonom innerhalb der SHOT-Sequenz.
        self.pusher_pub = self.create_publisher(
            Float64MultiArray,
            "/pusher_controller/commands",
            10,  # Pusher Servo (löst SHOT in Hardware-Interface aus)
        )
        self.arming_pub = self.create_publisher(
            Float64MultiArray,
            "/arming_controller/commands",
            10,  # System Arming (Hardware Freigabe)
        )

        # Subscribers: Empfängt Tilt-Befehle
        # Queue Size 10 = Puffert eingehende Nachrichten
        self.create_subscription(
            Float64MultiArray, "/nerf/tilt", self.tilt_callback, 10
        )

        # Services: Bietet Fire-Service an
        self.create_service(Trigger, "/nerf/fire", self.fire_callback)

        # Parameters: Physikalische Grenzen in Joint-Space (rad)
        # = trigger_joint URDF-Limits; gilt für Sim UND echte Hardware
        # (NerfSystem clampt zusätzlich auf dieselbe Range).
        # ALT: 5.23 / 6.28 — Servo-Rohwerte, in der Sim ans Limit geclampt
        self.tilt_min = -0.52  # Unten
        self.tilt_max = 0.52   # Oben

        self.get_logger().info("Nerf Control Node Started")

        # Initialisierungs-Timer (einmalig nach 1s)
        # HINWEIS: Kann gelöscht werden wenn nicht benötigt
        self.init_timer = self.create_timer(1.0, self.init_callback)

    def init_callback(self):
        """
        Initialisiert Launcher-Position auf 'UP' (tilt_max, Joint-Space)
        Läuft nur einmal
        """
        # ALT: cmd.data = [6.28] — Servo-Rohwert
        self.get_logger().info(
            f"Initializing Launcher Position to UP ({self.tilt_max})..."
        )
        cmd = Float64MultiArray()
        cmd.data = [self.tilt_max]
        self.trigger_pub.publish(cmd)

        if self.auto_arm:
            self.get_logger().warn("AUTO-ARMING the system (Hardware Enable)...")
            cmd_arm = Float64MultiArray()
            cmd_arm.data = [1.0]
            self.arming_pub.publish(cmd_arm)
        else:
            self.get_logger().info(
                "System is DISARMED. Send ARM command or use Gamepad LB+RB."
            )

        # Timer zerstören damit er nur einmal läuft
        self.init_timer.cancel()
        self.get_logger().info("Initialization Complete.")

    def tilt_callback(self, msg):
        """
        Akzeptiert normalisierte Tilt-Werte [0.0 - 1.0]

        Mapping (Joint-Space):
        0.0 = Unten (-0.52 rad)
        0.5 = Horizontal (0.0 rad)
        1.0 = Oben (+0.52 rad)

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
        Service Callback: Löst einen Schuss über die Firmware-FSM aus.

        Sendet pusher_vel > 1.0, was im Hardware-Interface (nerf_system.cpp)
        als SHOT-Befehl an die Firmware-FSM weitergeleitet wird.
        Die FSM steuert die komplette Sequenz autonom:
        SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED

        WICHTIG: Kein time.sleep()! Die Firmware übernimmt das Timing.
        """
        self.get_logger().info("FIRE: Sending SHOT command to Firmware FSM")

        # Sende Schuss-Befehl über Pusher-Controller
        # pusher_vel > 1.0 löst "SHOT 80" im Hardware-Interface aus
        cmd_push = Float64MultiArray()
        cmd_push.data = [10.0]
        self.pusher_pub.publish(cmd_push)

        # Reset Pusher-Command nach kurzer Zeit (non-blocking Timer)
        self._reset_timer = self.create_timer(0.5, self._reset_pusher)

        response.success = True
        response.message = "Shot delegated to Firmware FSM"
        return response

    def _reset_pusher(self):
        """Setzt den Pusher-Command zurück auf 0 (einmalig)"""
        cmd = Float64MultiArray()
        cmd.data = [0.0]
        self.pusher_pub.publish(cmd)
        self._reset_timer.cancel()
        self.get_logger().info("FIRE: Pusher command reset")


def main(args=None):
    rclpy.init(args=args)
    node = NerfControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
