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
        self.pusher_active = False
        self.pusher_timer = 0

        # Tilt State
        self.tilt_pos = 6.28  # Start UP
        self.tilt_step = 0.05

        # Arming Logic
        self.arm_button_start_time = 0.0
        self.arming_hold_triggered = False

        # Debounce/Edge detection
        self.last_buttons = []
        self.last_axes = []

        self.create_timer(0.05, self.loop)

    def loop(self):
        # Handle Pusher Pulse
        if self.pusher_active:
            self.pusher_timer -= 1
            if self.pusher_timer <= 0:
                self.pusher_active = False
                self.publish_pusher(0.0)

    def joy_callback(self, msg):
        if not self.last_buttons:
            self.last_buttons = msg.buttons
            self.last_axes = msg.axes
            return

        def pressed(idx):
            return (
                idx < len(msg.buttons)
                and msg.buttons[idx] == 1
                and self.last_buttons[idx] == 0
            )

        # --- 1. Arming / Disarming ---
        # Requirement: D-Pad Disarms
        dpad_activity = False

        # Check standard D-Pad Axes (6, 7) if present
        if len(msg.axes) >= 8:
            if abs(msg.axes[6]) > 0.5 or abs(msg.axes[7]) > 0.5:
                dpad_activity = True

        # Check Buttons (12-15) as per User Map
        for b_idx in [12, 13, 14, 15]:
            if b_idx < len(msg.buttons) and msg.buttons[b_idx] == 1:
                dpad_activity = True

        if dpad_activity:
            if self.armed_state:
                self.armed_state = False
                self.publish_arming(0.0)
                self.get_logger().warn("DISARMED via D-Pad")
                self.arm_button_start_time = 0.0  # Reset hold timer if disarming

        # Requirement: LB + RB Held for 3s -> ARM
        # User Map: 4=LB, 5=RB
        if 5 < len(msg.buttons):
            lb_held = msg.buttons[4] == 1
            rb_held = msg.buttons[5] == 1

            if lb_held and rb_held:
                if self.arm_button_start_time == 0.0:
                    self.arm_button_start_time = time.time()
                elif time.time() - self.arm_button_start_time > 3.0:
                    if not self.arming_hold_triggered:
                        self.armed_state = not self.armed_state
                        val = 1.0 if self.armed_state else 0.0
                        self.publish_arming(val)
                        self.get_logger().info(f"Arming Toggle: {self.armed_state}")
                        self.arming_hold_triggered = True
            else:
                self.arm_button_start_time = 0.0
                self.arming_hold_triggered = False

                # --- 2. Tilt Controls (Only if NOT arming) ---
                # Tilt Down: LB (Single press/hold)
                # Tilt Up: RB (Single press/hold)

                if pressed(4):  # LB
                    self.tilt_pos = max(5.23, self.tilt_pos - self.tilt_step)
                    self.publish_trigger(self.tilt_pos)
                    self.get_logger().info(f"Tilt DOWN: {self.tilt_pos:.2f}")

                if pressed(5):  # RB
                    self.tilt_pos = min(6.28, self.tilt_pos + self.tilt_step)
                    self.publish_trigger(self.tilt_pos)
                    self.get_logger().info(f"Tilt UP: {self.tilt_pos:.2f}")

        # --- 3. Flywheel Speed (LT) ---
        # Requirement: "depending on how much LT is pressed"
        # User Map says LT is Button 6.
        # But "how much" -> Axis. Usually Axis 2 (L2) or Axis 5.

        flywheel_tgt = 0.0

        # Check Axis 2 (Standard LT Analog)
        if len(msg.axes) > 2:
            raw = msg.axes[2]
            # Standard Linux Xbox: 1.0 (Released) to -1.0 (Pressed)
            # Map to 0.0 - 1.0
            val = (1.0 - raw) / 2.0
            if val > 0.05:
                flywheel_tgt = val * 100.0

        # Fallback/Override: Digital Button 6 (LT) from User Map
        # If pressed, set to specific speed (e.g., 50%) if Axis didn't set it high
        if 6 < len(msg.buttons) and msg.buttons[6] == 1:
            # If axis is reading near 0, use button defaults
            if flywheel_tgt < 10.0:
                flywheel_tgt = 50.0

        self.publish_flywheel(flywheel_tgt)

        # --- 4. Fire (A) ---
        # Requirement: "shotting A" -> User Map: 0='A'
        if pressed(0):
            if self.armed_state and flywheel_tgt > 10.0:
                self.get_logger().info("FIRE!")
                self.pusher_active = True
                self.pusher_timer = 5  # 0.5s
                self.publish_pusher(20.0)
            elif pressed(0):  # Log why failed
                self.get_logger().warn("Cannot Fire: Check Arm/Flywheel")

        self.last_buttons = msg.buttons
        self.last_axes = msg.axes

    def publish_arming(self, val):
        msg = Float64MultiArray()
        msg.data = [float(val)]
        self.pub_arming.publish(msg)

    def publish_flywheel(self, speed):
        msg = Float64MultiArray()
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
