#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class EncoderMonitor(Node):
    def __init__(self):
        super().__init__("encoder_monitor")
        self.subscription = self.create_subscription(
            JointState, "/joint_states", self.listener_callback, 10
        )
        self.get_logger().info("Monitoring Encoder Positions...")
        self.get_logger().info("-------------------------------")

    def listener_callback(self, msg):
        # Create a dictionary for easy lookup
        positions = {}
        for name, pos in zip(msg.name, msg.position):
            positions[name] = pos

        # Get wheel positions (default to None if not found)
        left = positions.get("left_wheel_joint")
        right = positions.get("right_wheel_joint")

        if left is not None and right is not None:
            # Print formatted output with overwrite (carriage return)
            print(f"\rLeft: {left:10.4f}  |  Right: {right:10.4f}", end="", flush=True)


def main(args=None):
    rclpy.init(args=args)
    encoder_monitor = EncoderMonitor()
    try:
        rclpy.spin(encoder_monitor)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nMonitor stopped.")
        encoder_monitor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
