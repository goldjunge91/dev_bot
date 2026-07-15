#!/usr/bin/env python3
"""
Nerf Control Node - High-Level Launcher Control
================================================
Bietet High-Level ROS2 Interface für Nerf Launcher

Services:
- nerf/fire (Trigger) - Führt komplette Schuss-Sequenz aus

Topics (Subscribed):
- nerf/tilt (std_msgs/Float64) - Normalisierte Tilt-Position [0.0-1.0]
  * 0.0 = Unten (tilt_min rad, Joint-Space)
  * 0.5 = Horizontal (0.0 rad)
  * 1.0 = Oben (tilt_max rad)

Topics (Published):
- trigger_controller/commands - Tilt Servo Position (Radiant)
- pusher_controller/commands - Pusher Servo Geschwindigkeit

Alle Topic-/Service-Namen sind relativ — Namespacing/Remapping erfolgt im
Launch-File (siehe ros2_communication.md).

Schuss-Sequenz:
    Die komplette Sequenz wird an die Firmware-FSM delegiert.
    Der ROS2-Node sendet nur den SHOT-Befehl über den Pusher-Controller.
    Die FSM steuert autonom: SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Float64MultiArray
from std_srvs.srv import Trigger


class NerfControlNode(Node):
    def __init__(self):
        super().__init__("nerf_control_node")

        self.declare_parameter("auto_arm", False)
        self.auto_arm = self.get_parameter("auto_arm").value

        # Flywheel-Power (%) für den SHOT-Befehl an die Firmware-FSM.
        self.declare_parameter("shot_power", 10.0)
        self.shot_power = self.get_parameter("shot_power").value

        # Physikalische Tilt-Grenzen in Joint-Space (rad) = trigger_joint
        # URDF-Limits; gilt für Sim UND echte Hardware (NerfSystem clampt
        # zusätzlich auf dieselbe Range — einzige Quelle der Wahrheit ist
        # das URDF, dies hier ist nur der Software-Default).
        self.declare_parameter("tilt_min", -0.52)
        self.declare_parameter("tilt_max", 0.52)
        self.tilt_min = self.get_parameter("tilt_min").value
        self.tilt_max = self.get_parameter("tilt_max").value

        # Grundstellung beim Start: normalisiert [0.0-1.0], gleiche Skala wie
        # nerf/tilt (0.0=unten, 0.5=horizontal, 1.0=oben). Default horizontal
        # statt "voll oben" — ein Launcher, der beim Hochfahren immer erst
        # steil nach oben fährt, ist unpraktisch/unerwartet.
        self.declare_parameter("init_tilt_norm", 0.5)
        self.init_tilt_norm = self.get_parameter("init_tilt_norm").value

        # Publishers: Steuern Hardware-Controller
        # Queue Size 10 = Puffert max. 10 Befehle, alte werden verworfen
        self.trigger_pub = self.create_publisher(
            Float64MultiArray,
            "trigger_controller/commands",
            10,  # Tilt Servo
        )
        self.pusher_pub = self.create_publisher(
            Float64MultiArray,
            "pusher_controller/commands",
            10,  # Pusher Servo (löst SHOT in Hardware-Interface aus)
        )
        self.arming_pub = self.create_publisher(
            Float64MultiArray,
            "arming_controller/commands",
            10,  # System Arming (Hardware Freigabe)
        )

        # Subscribers: Empfängt Tilt-Befehle
        # Queue Size 10 = Puffert eingehende Nachrichten
        self.create_subscription(
            Float64, "nerf/tilt", self.tilt_callback, 10
        )

        # Services: Bietet Fire-Service an
        self.create_service(Trigger, "nerf/fire", self.fire_callback)

        self.get_logger().info("Nerf Control Node Started")

        # Initialisierungs-Timer (einmalig nach 1s)
        self.init_timer = self.create_timer(1.0, self.init_callback)

        # Reset-Timer für fire_callback: einmalig angelegt und deaktiviert,
        # bei jedem Schuss per reset() neu gestartet. Vermeidet einen neuen
        # Timer (+ Leak, da destroy_timer() nie aufgerufen wurde) pro Schuss.
        self._reset_timer = self.create_timer(0.5, self._reset_pusher)
        self._reset_timer.cancel()

    def init_callback(self):
        """
        Fährt den Launcher auf die konfigurierte Grundstellung
        (init_tilt_norm, Default: horizontal). Läuft nur einmal.
        """
        target_phys = self._norm_to_phys(self.init_tilt_norm)
        self.get_logger().info(
            f"Initializing Launcher Position to {self.init_tilt_norm} "
            f"-> {target_phys:.2f} rad..."
        )
        cmd = Float64MultiArray()
        cmd.data = [target_phys]
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

        # Timer zerstören damit er nur einmal läuft (cancel() allein hält
        # das Timer-Objekt am Leben, ohne dass es je wieder feuert)
        self.init_timer.cancel()
        self.destroy_timer(self.init_timer)
        self.get_logger().info("Initialization Complete.")

    def _norm_to_phys(self, norm):
        """Mappt einen normalisierten Tilt-Wert [0.0-1.0] auf Joint-Space rad.

        0.0 = Unten (tilt_min rad), 0.5 = Horizontal (0.0 rad),
        1.0 = Oben (tilt_max rad).
        """
        norm = max(0.0, min(1.0, norm))
        return self.tilt_min + (norm * (self.tilt_max - self.tilt_min))

    def tilt_callback(self, msg):
        """
        Akzeptiert einen normalisierten Tilt-Wert [0.0 - 1.0]

        Beispiel:
        - msg.data = 0.0 → Launcher zeigt nach unten
        - msg.data = 1.0 → Launcher zeigt nach oben
        """
        target_phys = self._norm_to_phys(msg.data)

        cmd = Float64MultiArray()
        cmd.data = [target_phys]
        self.trigger_pub.publish(cmd)
        self.get_logger().debug(
            f"Tilt Command: {msg.data} -> Physical: {target_phys:.2f}"
        )

    def fire_callback(self, request, response):
        """
        Service Callback: Löst einen Schuss über die Firmware-FSM aus.

        Sendet pusher_vel = shot_power (Parameter, Default 10.0 %), was im
        Hardware-Interface (nerf_system.cpp) als SHOT-Befehl an die
        Firmware-FSM weitergeleitet wird.
        Die FSM steuert die komplette Sequenz autonom:
        SPINNING_UP → PUSHING → BRAKING → COOLDOWN → ARMED

        WICHTIG: Kein time.sleep()! Die Firmware übernimmt das Timing.
        """
        self.get_logger().info(f"FIRE: Sending SHOT {self.shot_power} to Firmware FSM")

        # Sende Schuss-Befehl über Pusher-Controller
        # pusher_vel > 0 löst "SHOT <shot_power>" im Hardware-Interface aus
        cmd_push = Float64MultiArray()
        cmd_push.data = [self.shot_power]
        self.pusher_pub.publish(cmd_push)

        # Reset Pusher-Command nach kurzer Zeit (wiederverwendeter Timer,
        # siehe __init__ — kein neuer Timer pro Schuss)
        self._reset_timer.reset()

        response.success = True
        response.message = "Shot delegated to Firmware FSM"
        return response

    def _reset_pusher(self):
        """Setzt den Pusher-Command zurück auf 0 und deaktiviert den Reset-Timer."""
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
