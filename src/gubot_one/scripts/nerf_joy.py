#!/usr/bin/env python3
"""
Nerf Launcher Joystick Control Node
====================================
Steuert den Nerf-Launcher über einen Xbox/PlayStation Controller.

Hauptfunktionen:
- Arming/Disarming System (LB+RB für 3s halten)
- Tilt Servo Steuerung (LB/RB einzeln)
- Feuer-Befehl (A-Taste)
- Notfall-Disarm (D-Pad beliebige Richtung)

Button Mapping (Xbox Controller):
- 0: A (Fire)
- 4: LB (Tilt Down / Arming)
- 5: RB (Tilt Up / Arming)
- 6: LT (Flywheel Speed - digital fallback)
- 12-15: D-Pad (Emergency Disarm)

Axis Mapping:
- Axis 6/7: D-Pad Axes (Emergency Disarm)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray
import time


class NerfJoy(Node):
    def __init__(self):
        super().__init__("nerf_joy")

        # Subscriber: Empfängt Joystick-Eingaben
        # Queue Size 10 = Puffert max. 10 Nachrichten
        self.subscription = self.create_subscription(Joy, "joy", self.joy_callback, 10)

        # Publisher: Steuert verschiedene Launcher-Komponenten
        # Queue Size 10 = Gut für Echtzeit-Steuerung, alte Befehle werden verworfen
        self.pub_arming = self.create_publisher(
            Float64MultiArray,
            "/arming_controller/commands",
            10,  # Arming/Disarming (Sicherheitssystem)
        )
        self.pub_shooter = self.create_publisher(
            Float64MultiArray,
            "/shooter_controller/commands",
            10,  # Shooter (Schussmechanismus)
        )
        self.pub_tilt = self.create_publisher(
            Float64MultiArray,
            "/tilt_controller/commands",
            10,  # Tilt Servo (Neigungswinkel)
        )

        # State Variables
        self.armed_state = False  # Sicherheitszustand: False=Disarmed, True=Armed
        self.pusher_active = False  # Pusher aktiv (während Schuss)
        self.pusher_timer = 0  # Timer für Pusher-Puls (0.5s)

        # Tilt State
        self.tilt_pos = 6.28  # Startposition: UP (360°)
        self.tilt_step = 0.05  # Schrittweite für Tilt-Änderungen

        # Arming Logic
        self.arm_button_start_time = 0.0  # Zeitpunkt wenn LB+RB gedrückt
        self.arming_hold_triggered = False  # Verhindert mehrfaches Triggern

        # Debounce/Edge detection
        self.last_buttons = []  # Vorheriger Button-Zustand
        self.last_axes = []  # Vorheriger Achsen-Zustand

        # Timer: Läuft mit 20Hz (0.05s) für Pusher-Puls-Verwaltung
        self.create_timer(0.05, self.loop)

    def loop(self):
        """
        Timer-Callback: Verwaltet Pusher-Puls
        """
        # Handle Pusher Pulse
        if self.pusher_active:
            self.pusher_timer -= 1
            if self.pusher_timer <= 0:
                self.pusher_active = False
                self.publish_shooter(0.0)  # Stoppe Pusher nach 0.5s

    def joy_callback(self, msg):
        """
        Hauptlogik: Verarbeitet alle Joystick-Eingaben

        Prioritäten:
        1. D-Pad → Notfall-Disarm (höchste Priorität)
        2. LB+RB (3s) → Arming Toggle
        3. LB/RB einzeln → Tilt Control (nur wenn nicht arming)
        4. A → Fire (nur wenn armed)
        """
        # Initialisierung beim ersten Durchlauf
        if not self.last_buttons:
            self.last_buttons = msg.buttons
            self.last_axes = msg.axes
            return

        def pressed(idx):
            """Erkennt Button-Press (Flanke 0→1)"""
            return (
                idx < len(msg.buttons)
                and msg.buttons[idx] == 1
                and self.last_buttons[idx] == 0
            )

        # --- 1. Arming / Disarming ---
        # Anforderung: D-Pad disarmt sofort (Notfall-Stopp)
        dpad_activity = False

        # Prüfe Standard D-Pad Achsen (6, 7) falls vorhanden
        if len(msg.axes) >= 8:
            if abs(msg.axes[6]) > 0.5 or abs(msg.axes[7]) > 0.5:
                dpad_activity = True

        # Prüfe Buttons (12-15) gemäß User Map
        for b_idx in [12, 13, 14, 15]:
            if b_idx < len(msg.buttons) and msg.buttons[b_idx] == 1:
                dpad_activity = True

        if dpad_activity:
            if self.armed_state:
                self.armed_state = False
                self.publish_arming(0.0)
                self.get_logger().warn("DISARMED via D-Pad")
                self.arm_button_start_time = 0.0  # Reset hold timer if disarming

        # Anforderung: LB + RB für 3s gehalten → ARM/DISARM Toggle
        # User Map: 4=LB, 5=RB
        if 5 < len(msg.buttons):
            lb_held = msg.buttons[4] == 1
            rb_held = msg.buttons[5] == 1

            if lb_held and rb_held:
                # Beide Buttons gedrückt: Starte/Update Timer
                if self.arm_button_start_time == 0.0:
                    self.arm_button_start_time = time.time()
                elif time.time() - self.arm_button_start_time > 3.0:
                    # 3 Sekunden erreicht: Toggle Arming
                    if not self.arming_hold_triggered:
                        self.armed_state = not self.armed_state
                        val = 1.0 if self.armed_state else 0.0
                        self.publish_arming(val)
                        self.get_logger().info(f"Arming Toggle: {self.armed_state}")
                        self.arming_hold_triggered = True
            else:
                # Buttons losgelassen: Reset Timer
                self.arm_button_start_time = 0.0
                self.arming_hold_triggered = False

                # --- 2. Tilt Controls (Nur wenn NICHT arming) ---
                # Tilt Down: LB (Einzeldruck/Halten)
                # Tilt Up: RB (Einzeldruck/Halten)

                if pressed(4):  # LB
                    self.tilt_pos = max(5.23, self.tilt_pos - self.tilt_step)
                    self.publish_tilt(self.tilt_pos)
                    self.get_logger().info(f"Tilt DOWN: {self.tilt_pos:.2f}")

                if pressed(5):  # RB
                    self.tilt_pos = min(6.28, self.tilt_pos + self.tilt_step)
                    self.publish_tilt(self.tilt_pos)
                    self.get_logger().info(f"Tilt UP: {self.tilt_pos:.2f}")

        # --- 3. Fire (A) ---
        # Anforderung: "Schießen mit A" → User Map: 0='A'
        if pressed(0):
            # Sicherheitsprüfungen: Armed
            if self.armed_state:
                self.get_logger().info("FIRE!")
                self.pusher_active = True
                self.pusher_timer = 5  # 0.5s bei 20Hz (5 * 0.05s)
                self.publish_shooter(10.0)
            else:
                self.get_logger().warn("Cannot Fire: System not Armed")

        # Speichere aktuellen Zustand für nächste Iteration
        self.last_buttons = msg.buttons
        self.last_axes = msg.axes

    def publish_arming(self, val):
        """Sendet Arming-Befehl (0.0=Disarm, 1.0=Arm)"""
        msg = Float64MultiArray()
        msg.data = [float(val)]
        self.pub_arming.publish(msg)

    def publish_shooter(self, power):
        """Sendet Shooter-Befehl (Flywheel Power %)"""
        msg = Float64MultiArray()
        msg.data = [float(power)]
        self.pub_shooter.publish(msg)

    def publish_tilt(self, pos):
        """
        Sendet Tilt-Servo Position in Radiant
        5.23 rad ≈ 300° (DOWN), 6.28 rad ≈ 360° (UP)
        """
        msg = Float64MultiArray()
        msg.data = [float(pos)]
        self.pub_tilt.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = NerfJoy()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
