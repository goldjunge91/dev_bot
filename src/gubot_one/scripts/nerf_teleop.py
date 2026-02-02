#!/usr/bin/env python3

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
   3 : Stop Flywheels
   4 : Spin Flywheels (Normal)
   5 : Spin Flywheels (Turbo)
   
   SPACE : Fire Single Shot (Pulse Pusher)
   
   t : Trigger Servo (Open)
   g : Trigger Servo (Close)

CTRL-C to quit
"""

moveBindings = {
    "w": (0.5, 0.0),
    "s": (-0.5, 0.0),
    "a": (0.0, 1.0),
    "d": (0.0, -1.0),
}

settings = termios.tcgetattr(sys.stdin)


def getKey():
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

        self.pub_cmd_vel = self.create_publisher(Twist, "/cmd_vel", 10)
        self.pub_arming = self.create_publisher(
            Float64MultiArray, "/arming_controller/commands", 10
        )
        self.pub_flywheel = self.create_publisher(
            Float64MultiArray, "/flywheel_controller/commands", 10
        )
        self.pub_pusher = self.create_publisher(
            Float64MultiArray, "/pusher_controller/commands", 10
        )
        self.pub_trigger = self.create_publisher(
            Float64MultiArray, "/trigger_controller/commands", 10
        )

        self.timer = self.create_timer(0.1, self.loop)

        self.speed = 0.0
        self.turn = 0.0
        self.armed = False
        self.flywheel_speed = 0.0
        self.pusher_active = False
        self.pusher_timer = 0

        print(msg)

    def loop(self):
        key = getKey()

        # Movement
        if key in moveBindings.keys():
            self.speed = moveBindings[key][0]
            self.turn = moveBindings[key][1]
        elif key == " " or key == "k":
            self.speed = 0.0
            self.turn = 0.0
        else:
            self.speed = 0.0
            self.turn = 0.0

        # Launcher
        if key == "1":
            self.get_logger().info("Disarming...")
            self.publish_arming(0.0)
        elif key == "2":
            self.get_logger().info("ARMING SYSTEM!")
            self.publish_arming(1.0)

        elif key == "3":
            self.get_logger().info("Stopping Flywheels")
            self.flywheel_speed = 0.0
            self.publish_flywheel(0.0)

        elif key == "4":
            self.get_logger().info("Spinning Up (Normal)")
            self.flywheel_speed = 50.0  # Adjust based on motor curve
            self.publish_flywheel(self.flywheel_speed)

        elif key == "5":
            self.get_logger().info("Spinning Up (Turbo)")
            self.flywheel_speed = 100.0
            self.publish_flywheel(self.flywheel_speed)

        elif key == " ":
            if not self.pusher_active:
                self.get_logger().info("FIRING!")
                self.pusher_active = True
                self.pusher_timer = 5  # 0.5 seconds at 10Hz
                self.publish_pusher(15.0)

        elif key == "t":
            self.publish_trigger(0.5)
        elif key == "g":
            self.publish_trigger(0.0)

        elif key == "\x03":  # CTRL-C
            self.publish_twist(0.0, 0.0)
            sys.exit()

        # Continuous publishing
        self.publish_twist(self.speed, self.turn)

        # Handle Pusher Pulse
        if self.pusher_active:
            self.pusher_timer -= 1
            if self.pusher_timer <= 0:
                self.pusher_active = False
                self.publish_pusher(0.0)

    def publish_twist(self, linear, angular):
        twist = Twist()
        twist.linear.x = float(linear)
        twist.angular.z = float(angular)
        self.pub_cmd_vel.publish(twist)

    def publish_arming(self, val):
        msg = Float64MultiArray()
        msg.data = [float(val)]
        self.pub_arming.publish(msg)

    def publish_flywheel(self, speed):
        msg = Float64MultiArray()
        # Assuming left is positive, right is negative for counter-rotation
        msg.data = [float(speed), float(-speed)]
        self.pub_flywheel.publish(msg)

    def publish_pusher(self, speed):
        msg = Float64MultiArray()
        msg.data = [float(speed)]
        self.pub_pusher.publish(msg)

    def publish_trigger(self, pos):
        msg = Float64MultiArray()
        msg.data = [float(pos)]
        self.pub_trigger.publish(msg)


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
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == "__main__":
    main()
