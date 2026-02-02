#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64MultiArray
import time


class NerfJoy(Node):
    def __init__(self):
        super().__init__("nerf_joy")

        self.subscription = self.create_subscription(Joy, "joy", self.joy_callback, 10)

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

        # State
        self.armed_state = False
        self.flywheel_state = False
        self.trigger_state = False
        self.turbo_state = False
        self.pusher_active = False
        self.pusher_start_time = 0.0

        # Debounce/Edge detection
        self.last_buttons = []

    def joy_callback(self, msg):
        # Initialize last_buttons if empty
        if not self.last_buttons:
            self.last_buttons = msg.buttons
            return

        # Button Mappings (Standard Xbox/Logitech)
        # 0: A/Green (Fire)
        # 1: B/Red (Arm)
        # 2: X/Blue (Flywheel)
        # 3: Y/Yellow (Trigger Servo)
        # 4: LB
        # 5: RB (Turbo Hold)

        # Helper to detect rising edge
        def pressed(idx):
            return msg.buttons[idx] == 1 and self.last_buttons[idx] == 0

        # --- Arming (Toggle) [B] ---
        if pressed(1):
            self.armed_state = not self.armed_state
            val = 1.0 if self.armed_state else 0.0
            self.publish_arming(val)
            self.get_logger().info(f"Arming: {self.armed_state}")

        # --- Flywheels (Toggle) [X] ---
        if pressed(2):
            self.flywheel_state = not self.flywheel_state
            self.update_flywheels(msg)
            self.get_logger().info(f"Flywheels: {self.flywheel_state}")

        # Check Turbo Hold [RB]
        # (Update flywheels if state changed while holding/releasing turbo)
        if msg.buttons[5] != self.last_buttons[5] and self.flywheel_state:
            self.update_flywheels(msg)

        # --- Fire (Pulse) [A] ---
        if pressed(0):
            if not self.pusher_active:
                self.get_logger().info("FIRE!")
                self.pusher_active = True
                self.pusher_start_time = time.time()
                self.publish_pusher(15.0)  # Velocity

        # --- Trigger Servo (Toggle) [Y] ---
        if pressed(3):
            self.trigger_state = not self.trigger_state
            val = 0.5 if self.trigger_state else 0.0  # Open/Close
            self.publish_trigger(val)
            self.get_logger().info(f"Trigger Servo: {self.trigger_state}")

        # Update last state
        self.last_buttons = msg.buttons

        # Handle Pusher Timer
        if self.pusher_active:
            if time.time() - self.pusher_start_time > 0.5:  # 0.5 sec pulse
                self.pusher_active = False
                self.publish_pusher(0.0)

    def update_flywheels(self, joy_msg):
        if not self.flywheel_state:
            self.publish_flywheel(0.0)
            return

        speed = 50.0
        if joy_msg.buttons[5] == 1:  # RB held for turbo
            speed = 100.0

        self.publish_flywheel(speed)

    def publish_arming(self, val):
        msg = Float64MultiArray()
        msg.data = [float(val)]
        self.pub_arming.publish(msg)

    def publish_flywheel(self, speed):
        msg = Float64MultiArray()
        msg.data = [float(speed), float(-speed)]  # Counter-rotating
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
    node = NerfJoy()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
