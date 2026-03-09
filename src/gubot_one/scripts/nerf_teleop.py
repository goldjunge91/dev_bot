#!/usr/bin/env python3
"""
Nerf Launcher Keyboard Teleop Node
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
    T - Tilt UP (6.28 rad)
    G - Tilt DOWN (5.23 rad)
    R / F - Power UP/DN (5% steps)
    E / D - Power UP/DN (1% steps)
"""

import sys
import termios
import tty
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
   a    s    d

Launcher Controls:
   1 : Disarm System
   2 : ARM System
   
   SPACE : Fire Single Shot (Pulse Pusher)
   
   t : Tilt Servo (UP - 6.28)
   g : Tilt Servo (DOWN - 5.23)
   
   r / f : Increase/Decrease Fire Power (5% steps)
   e / b : Increase/Decrease Fire Power (1% steps)

CTRL-C to quit
"""

moveBindings = {
    "w": (0.5, 0.0),  # Vorwärts: linear_x=0.5, angular_z=0.0
    "s": (-0.5, 0.0),  # Rückwärts: linear_x=-0.5
    "a": (0.0, 1.0),  # Links drehen: angular_z=1.0
    "d": (0.0, -1.0),  # Rechts drehen: angular_z=-1.0
}

# Terminal-Einstellungen speichern für Wiederherstellung
settings = termios.tcgetattr(sys.stdin)


def getKey():
    """
    Liest einzelne Tastatureingabe ohne Enter
    Timeout: 0.1s (non-blocking)
    """
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
        self.pub_cmd_vel = self.create_publisher(Twist, "/cmd_vel", 10)

        # Publisher: Nerf Launcher Komponenten
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
        self.speed = 0.0  # Linear-Geschwindigkeit
        self.turn = 0.0  # Winkel-Geschwindigkeit
        self.armed = False  # Arming-Status
        self.pusher_active = False  # Pusher aktiv während Schuss
        self.pusher_timer = 0  # Timer für Pusher-Puls
        self.tilt_pos = 6.28  # Startposition: UP (360°)
        self.tilt_step = 0.05  # Schrittweite für Tilt
        self.shot_power = 5.0  # Standard Schuss-Power (0-100)
        self.input_count = 0  # Zähler für Reprints
        self.max_inputs = 15  # Reprint nach 15 Eingaben

        print(msg)  # Zeige Hilfe-Text

    def loop(self):
        """
        Hauptschleife: Liest Tastatur und steuert Roboter + Launcher
        Läuft mit 10Hz
        """
        key = getKey()

        # Bewegungs-Steuerung
        if key in moveBindings.keys():
            self.input_count += 1
            self.speed = moveBindings[key][0]
            self.turn = moveBindings[key][1]
        elif key == " ":  # SPACE wird unten für Schuss/Stopp behandelt
            pass
        elif key == "k":
            self.input_count += 1
            self.speed = 0.0
            self.turn = 0.0
        else:
            self.speed = 0.0
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
            self.turn = 0.0

        elif key == "t":  # Tilt UP
            self.input_count += 1
            self.tilt_pos = min(6.28, self.tilt_pos + self.tilt_step)
            self.get_logger().info(f"Tilt UP: {self.tilt_pos:.2f}")
            self.publish_tilt(self.tilt_pos)
        elif key == "g":  # Tilt DOWN
            self.input_count += 1
            self.tilt_pos = max(5.23, self.tilt_pos - self.tilt_step)
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
            self.publish_twist(0.0, 0.0)
            sys.exit()

        # Kontinuierliches Publizieren der Bewegung
        self.publish_twist(self.speed, self.turn)

        # Verwalte Pusher-Puls
        if self.pusher_active:
            self.pusher_timer -= 1
            if self.pusher_timer <= 0:
                self.pusher_active = False
                self.publish_shooter(0.0)  # Stoppe Pusher/Sequenz reset

    def publish_twist(self, linear, angular):
        twist = Twist()
        twist.linear.x = float(linear)
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
        node.publish_twist(0.0, 0.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == "__main__":
    main()
