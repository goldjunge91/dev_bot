#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
import time
import math


class FullSystemTest(Node):
    def __init__(self):
        super().__init__("full_system_test")

        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist, "/diff_cont/cmd_vel_unstamped", 10
        )
        self.trigger_pub = self.create_publisher(
            Float64MultiArray, "/trigger_controller/commands", 10
        )

        # Subscribers
        self.create_subscription(JointState, "/joint_states", self.joint_callback, 10)

        # Services
        self.fire_client = self.create_client(Trigger, "/nerf/fire")

        self.wheel_vels = {}
        self.get_logger().info("Full System Test Node Started")

    def joint_callback(self, msg):
        for name, vel in zip(msg.name, msg.velocity):
            self.wheel_vels[name] = vel

    def run_base_test(self):
        self.get_logger().info("--- STARTING BASE TEST ---")

        # Move Forward
        msg = Twist()
        msg.linear.x = 0.2
        self.get_logger().info("Moving Forward at 0.2 m/s...")
        end_time = time.time() + 2.0
        while time.time() < end_time:
            self.cmd_vel_pub.publish(msg)
            # Check feedback
            left_vel = self.wheel_vels.get("left_wheel_joint", 0.0)
            right_vel = self.wheel_vels.get("right_wheel_joint", 0.0)
            self.get_logger().info(
                f"Encoders: L={left_vel:.2f}, R={right_vel:.2f}",
                throttle_duration_sec=0.5,
            )
            time.sleep(0.1)

        # Stop
        msg.linear.x = 0.0
        self.cmd_vel_pub.publish(msg)
        self.get_logger().info("Stopping Base.")
        time.sleep(1.0)

    def run_nerf_test(self):
        self.get_logger().info("--- STARTING NERF TEST ---")

        # Test Tilt
        targets = [5.23, 6.28, 5.75]  # Down, Up, Middle
        for t in targets:
            self.get_logger().info(f"Tilting to {t:.2f} rad")
            cmd = Float64MultiArray()
            cmd.data = [t]
            self.trigger_pub.publish(cmd)
            time.sleep(2.0)

        # Test Fire
        self.get_logger().info("Testing Fire Sequence...")
        if self.fire_client.wait_for_service(timeout_sec=2.0):
            req = Trigger.Request()
            future = self.fire_client.call_async(req)
            rclpy.spin_until_future_complete(self, future)
            self.get_logger().info(f"Fire Result: {future.result().message}")
        else:
            self.get_logger().error("Fire Service not available!")


def main():
    rclpy.init()
    node = FullSystemTest()

    try:
        # Run tests in separate thread or simple block since we are script
        node.run_base_test()
        node.run_nerf_test()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
