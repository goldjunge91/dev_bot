#!/usr/bin/env python3

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

"""
Nerf Launcher Keyboard Teleop Node.

===================================
Tastatur-Steuerung für Gubot One + Nerf Launcher

Funktionen:
- Roboter-Bewegung (WASD)
- Nerf Launcher Steuerung
- Arming/Disarming (1/2)
- Tilt Servo (T/G)
- Feuer-Befehl (SPACE)

Tastenbelegung:
  Bewegung:
    W - Vorwärts
    S - Rückwärts
    A - Links drehen
    D - Rechts drehen

  Launcher:
    1 - Disarm System
    2 - ARM System
    SPACE - Schießen
    T - Tilt UP (+0.52 rad)
    G - Tilt DOWN (-0.52 rad)
    R / F - Power UP/DN (5% steps)
    E / D - Power UP/DN (1% steps)
"""

import os
import sys
import termios
import tty
from collections import deque
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray
from select import select

msg = """
Control Gubot One + Nerf Launcher!
---------------------------
Moving around:
        w
   a    s    d       (A/D + Shift = Strafe Left/Right)

Launcher Controls:
   1 : Disarm System
   2 : ARM System

   SPACE : Fire Single Shot (Pulse Pusher)

   t : Tilt Servo (UP - +0.52)
   g : Tilt Servo (DOWN - -0.52)

   r / f : Increase/Decrease Fire Power (5% steps)
   e / b : Increase/Decrease Fire Power (1% steps)

    CTRL-C to quit
"""

moveBindings = {
    "w": (0.5, 0.0, 0.0),  # Vorwärts: x=0.5
    "s": (-0.5, 0.0, 0.0),  # Rückwärts: x=-0.5
    "a": (0.0, 0.0, 1.0),  # Links drehen: z=1.0
    "d": (0.0, 0.0, -1.0),  # Rechts drehen: z=-1.0
    "A": (0.0, 0.5, 0.0),  # Links strafen: y=0.5
    "D": (0.0, -0.5, 0.0),  # Rechts strafen: y=-0.5
}

# Test-Modus: scripted key sequence ohne TTY (für Integrationstests)
_TEST_MODE = os.environ.get("NERF_TELEOP_TEST_MODE", "0") == "1"
_TEST_KEY_QUEUE = deque(os.environ.get("NERF_TELEOP_TEST_KEYS", ""))

# Terminal-Einstellungen speichern für Wiederherstellung
# VORHER:
# settings = termios.tcgetattr(sys.stdin)
try:
    settings = termios.tcgetattr(sys.stdin) if sys.stdin.isatty() else None
except termios.error:
    settings = None


def getKey():
    """
    Liest einzelne Tastatureingabe ohne Enter.

    Timeout: 0.1s (non-blocking)
    """
    if _TEST_MODE:
        return _TEST_KEY_QUEUE.popleft() if _TEST_KEY_QUEUE else ""

    if settings is None or not sys.stdin.isatty():
        return ""

    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class NerfTeleop(Node):
    def __init__(self):
        super().__init__("nerf_teleop")

        # Publisher: Roboter-Bewegung
        # Queue Size 10 = Puffert max. 10 Bewegungsbefehle
        # self.pub_cmd_vel = self.create_publisher(Twist, "/cmd_vel", 10)
        self.pub_cmd_vel = self.create_publisher(Twist, "/cmd_vel_joy", 10)

        # Publisher: Nerf Launcher Komponenten
        # Queue Size 10 = Gut für Echtzeit-Steuerung
        self.pub_arming = self.create_publisher(
            Float64MultiArray,
            "/arming_controller/commands",
            10,  # Sicherheitssystem
        )
        self.pub_shooter = self.create_publisher(
            Float64MultiArray,
            "/shooter_controller/commands",
            10,  # Shooter (löst SHOT in Hardware aus)
        )
        self.pub_tilt = self.create_publisher(
            Float64MultiArray,
            "/tilt_controller/commands",
            10,  # Tilt Servo
        )

        # Timer: Läuft mit 10Hz für kontinuierliche Steuerung
        self.timer = self.create_timer(0.1, self.loop)

        # Zustandsvariablen
        self.speed = 0.0  # Linear-Geschwindigkeit X
        self.strafe = 0.0  # Linear-Geschwindigkeit Y (Mecanum)
        self.turn = 0.0  # Winkel-Geschwindigkeit
        self.armed = False  # Arming-Status
        self.pusher_active = False  # Pusher aktiv während Schuss
        self.pusher_timer = 0  # Timer für Pusher-Puls
        self.tilt_min = -0.52
        self.tilt_max = 0.52
        self.tilt_pos = 0.0

        self.tilt_step = 0.05  # Schrittweite für Tilt
        self.shot_power = 5.0  # Standard Schuss-Power (0-100)
        self.input_count = 0  # Zähler für Reprints
        self.max_inputs = 15  # Reprint nach 15 Eingaben

        print(msg)  # Zeige Hilfe-Text

    def loop(self):
        """
        Hauptschleife: Liest Tastatur und steuert Roboter + Launcher.

        Läuft mit 10Hz
        """
        key = getKey()

        # Bewegungs-Steuerung
        if key in moveBindings.keys():
            self.input_count += 1
            self.speed = moveBindings[key][0]
            self.strafe = moveBindings[key][1]
            self.turn = moveBindings[key][2]
        elif key == " ":  # SPACE wird unten für Schuss/Stopp behandelt
            pass
        elif key == "k":
            self.input_count += 1
            self.speed = 0.0
            self.strafe = 0.0
            self.turn = 0.0
        else:
            self.speed = 0.0
            self.strafe = 0.0
            self.turn = 0.0
            # Keine Erhöhung von input_count bei leeren/unbekannten Tasten

        # Launcher-Steuerung
        if key == "1":
            self.input_count += 1
            self.get_logger().info("Disarming...")
            self.publish_arming(0.0)
        elif key == "2":
            self.input_count += 1
            self.get_logger().info("ARMING SYSTEM!")
            self.publish_arming(1.0)

        elif key == " ":  # SPACE = Feuer (und Stopp oben)
            if not self.pusher_active:
                self.input_count += 1
                self.get_logger().info(f"FIRING (Power: {self.shot_power:.1f}%)!")
                self.pusher_active = True
                self.pusher_timer = 5  # 0.5 Sekunden bei 10Hz
                self.publish_shooter(self.shot_power)

            # Stoppe Bewegung bei SPACE
            self.speed = 0.0
            self.strafe = 0.0
            self.turn = 0.0

        elif key == "t":  # Tilt UP
            self.input_count += 1
            # Normalisierte Richtung: UP = Positiv
            self.tilt_pos = min(self.tilt_max, self.tilt_pos + self.tilt_step)
            self.get_logger().info(f"Tilt UP: {self.tilt_pos:.2f}")
            self.publish_tilt(self.tilt_pos)
        elif key == "g":  # Tilt DOWN
            self.input_count += 1
            # Normalisierte Richtung: DOWN = Negativ
            self.tilt_pos = max(self.tilt_min, self.tilt_pos - self.tilt_step)
            self.get_logger().info(f"Tilt DOWN: {self.tilt_pos:.2f}")
            self.publish_tilt(self.tilt_pos)
        elif key == "r":  # Power UP 5%
            self.input_count += 1
            self.shot_power = min(100.0, self.shot_power + 5.0)
            self.get_logger().info(f"Shot Power: {self.shot_power:.1f}% (+5%)")
        elif key == "f":  # Power DOWN 5%
            self.input_count += 1
            self.shot_power = max(0.0, self.shot_power - 5.0)
            self.get_logger().info(f"Shot Power: {self.shot_power:.1f}% (-5%)")
        elif key == "e":  # Power UP 1%
            self.input_count += 1
            self.shot_power = min(100.0, self.shot_power + 1.0)
            self.get_logger().info(f"Shot Power: {self.shot_power:.1f}% (+1%)")
        elif key == "b":  # Power DOWN 1%
            self.input_count += 1
            self.shot_power = max(0.0, self.shot_power - 1.0)
            self.get_logger().info(f"Shot Power: {self.shot_power:.1f}% (-1%)")

        # Periodischer Reprint der Hilfe
        if self.input_count >= self.max_inputs:
            print(msg)
            print(f"--- Current Status: Power Level = {self.shot_power:.1f}% ---")
            self.input_count = 0

        elif key == "\x03":  # CTRL-C = Beenden
            self.publish_twist(0.0, 0.0, 0.0)
            sys.exit()

        # Kontinuierliches Publizieren der Bewegung
        self.publish_twist(self.speed, self.strafe, self.turn)

        # Verwalte Pusher-Puls
        if self.pusher_active:
            self.pusher_timer -= 1
            if self.pusher_timer <= 0:
                self.pusher_active = False
                self.publish_shooter(0.0)  # Stoppe Pusher/Sequenz reset

    def publish_twist(self, linear_x, linear_y, angular):
        twist = Twist()
        twist.linear.x = float(linear_x)
        twist.linear.y = float(linear_y)
        twist.angular.z = float(angular)
        self.pub_cmd_vel.publish(twist)

    def publish_arming(self, val):
        msg = Float64MultiArray()
        msg.data = [float(val)]
        self.pub_arming.publish(msg)

    def publish_shooter(self, power):
        msg = Float64MultiArray()
        msg.data = [float(power)]
        self.pub_shooter.publish(msg)

    def publish_tilt(self, pos):
        msg = Float64MultiArray()
        msg.data = [float(pos)]
        self.pub_tilt.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = NerfTeleop()
    try:
        rclpy.spin(node)
    except Exception as e:
        print(e)
    finally:
        node.publish_twist(0.0, 0.0, 0.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if settings is not None and sys.stdin.isatty():
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == "__main__":
    main()
