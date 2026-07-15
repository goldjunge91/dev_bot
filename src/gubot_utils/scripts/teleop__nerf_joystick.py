#!/usr/bin/env python3
"""
Nerf Launcher Joystick Control Node
====================================
Steuert den Nerf-Launcher über einen Xbox/PlayStation Controller.

Hauptfunktionen:
- Arming/Disarming System (LB+RB für 3s halten)
- Tilt Servo Steuerung (LB/RB einzeln)
- Feuer-Befehl (RT)
- Notfall-Disarm (D-Pad beliebige Richtung)

Button Mapping (Xbox Controller):
- 4: LB (Tilt Down / Arming)
- 5: RB (Tilt Up / Arming)
- 6: LT (Flywheel Speed - digital fallback)
- 7: RT (Fire - digital fallback)
- 12-15: D-Pad (Emergency Disarm)

Axis Mapping:
- Axis 5: RT analog (Fire; Ruhe +1.0, gedrückt -1.0)
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
            10,  # Shooter/Pusher (Schussmechanismus)
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

        # Tilt State — Joint-Space (rad), = trigger_joint URDF-Limits ±0.52.
        # Gilt für Sim UND echte Hardware (NerfSystem clampt auf dieselbe Range).
        self.tilt_min = -0.52  # DOWN
        self.tilt_max = 0.52  # UP
        self.tilt_pos = self.tilt_max  # Startposition: UP
        self.tilt_step = 0.05  # Schrittweite für Tilt-Änderungen

        # Arming Logic
        self.arm_button_start_time = 0.0  # Zeitpunkt wenn LB+RB gedrückt
        self.arming_hold_triggered = False  # Verhindert mehrfaches Triggern

        # Debounce/Edge detection
        self.last_buttons = []  # Vorheriger Button-Zustand
        self.last_axes = []  # Vorheriger Achsen-Zustand
        self.last_rt_pressed = False  # Vorheriger RT-Zustand (Flanken-Erkennung)

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
                self.publish_shooter(0.0)  # Stoppe Shooter/Pusher nach 0.5s

    def joy_callback(self, msg):
        """
        Hauptlogik: Verarbeitet alle Joystick-Eingaben

        Prioritäten:
        1. D-Pad → Notfall-Disarm (höchste Priorität)
        2. LB+RB (3s) → Arming Toggle
        3. LB/RB einzeln → Tilt Control (nur wenn nicht arming)
        4. RT → Fire (nur wenn armed)
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

                # Joint-Space-Konvention: positiv = UP (Achse in
                # nerf_launcher.urdf.xacro entsprechend orientiert).
                # LB = Tilt Down (−step), RB = Tilt Up (+step) — wie im
                # Button-Mapping oben dokumentiert.
                if pressed(4):  # LB
                    self.tilt_pos = max(self.tilt_min, self.tilt_pos - self.tilt_step)
                    self.publish_tilt(self.tilt_pos)
                    self.get_logger().info(f"Tilt DOWN: {self.tilt_pos:.2f}")

                if pressed(5):  # RB
                    self.tilt_pos = min(self.tilt_max, self.tilt_pos + self.tilt_step)
                    self.publish_tilt(self.tilt_pos)
                    self.get_logger().info(f"Tilt UP: {self.tilt_pos:.2f}")

        # --- 3. Fire (RT) ---
        # Fire liegt bewusst NICHT auf A (Button 0): das ist der
        # teleop_twist_joy Deadman-Button (enable_button: 0) — Fahren-Enable
        # hätte im armed-Zustand jedes Mal einen Schuss ausgelöst.
        # RT wird doppelt erkannt: analoge Achse 5 (Ruhe +1.0, voll gedrückt
        # -1.0) ODER digitaler Button 7 (Fallback für Controller, die die
        # Trigger als Buttons melden).
        rt_pressed = False
        if len(msg.axes) > 5 and msg.axes[5] < -0.5:
            rt_pressed = True
        if len(msg.buttons) > 7 and msg.buttons[7] == 1:
            rt_pressed = True

        if rt_pressed and not self.last_rt_pressed:
            # Sicherheitsprüfungen: Armed
            if self.armed_state:
                self.get_logger().info("FIRE!")
                self.pusher_active = True
                self.pusher_timer = 5  # 0.5s bei 20Hz (5 * 0.05s)
                self.publish_shooter(20.0)
            else:
                self.get_logger().warn("Cannot Fire: System not Armed")

        # Speichere aktuellen Zustand für nächste Iteration
        self.last_buttons = msg.buttons
        self.last_axes = msg.axes
        self.last_rt_pressed = rt_pressed

    def publish_arming(self, val):
        """Sendet Arming-Befehl (0.0=Disarm, 1.0=Arm)"""
        msg = Float64MultiArray()
        msg.data = [float(val)]
        self.pub_arming.publish(msg)

    def publish_shooter(self, speed):
        """Sendet Shooter/Pusher-Geschwindigkeit"""
        msg = Float64MultiArray()
        msg.data = [float(speed)]
        self.pub_shooter.publish(msg)

    def publish_tilt(self, pos):
        """
        Sendet Tilt-Servo Position in Radiant (Joint-Space)
        -0.52 rad = DOWN, +0.52 rad = UP
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
