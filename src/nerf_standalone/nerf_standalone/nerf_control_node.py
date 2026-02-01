#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger
import time


class NerfControlNode(Node):
    def __init__(self):
        super().__init__("nerf_control_node")

        # Publishers
        self.trigger_pub = self.create_publisher(
            Float64MultiArray, "/trigger_controller/commands", 10
        )
        self.flywheel_pub = self.create_publisher(
            Float64MultiArray, "/flywheel_controller/commands", 10
        )
        self.pusher_pub = self.create_publisher(
            Float64MultiArray, "/pusher_controller/commands", 10
        )

        # Subscribers
        self.create_subscription(
            Float64MultiArray, "/nerf/tilt", self.tilt_callback, 10
        )

        # Services
        self.create_service(Trigger, "/nerf/fire", self.fire_callback)

        # Parameters
        self.tilt_min = 5.23  # ~300 deg
        self.tilt_max = 6.28  # ~360 deg

        self.get_logger().info("Nerf Control Node Started")

    def tilt_callback(self, msg):
        """
        Accepts normalized tilt value [0.0 - 1.0]
        0.0 = Bottom (5.23)
        1.0 = Top (6.28)
        0.5 = Horizontal (5.75)
        """
        # Take the first element if array
        if len(msg.data) > 0:
            target_norm = msg.data[0]

            # Clamp input to 0-1
            target_norm = max(0.0, min(1.0, target_norm))

            # Map to physical angles
            target_phys = self.tilt_min + (
                target_norm * (self.tilt_max - self.tilt_min)
            )

            # Publish safely
            cmd = Float64MultiArray()
            cmd.data = [target_phys]
            self.trigger_pub.publish(cmd)
            self.get_logger().info(
                f"Tilt Command: {target_norm} -> Physical: {target_phys:.2f}"
            )

    def fire_callback(self, request, response):
        self.get_logger().info("FIRE SEQUENCE INITIATED")

        # 1. Spin up Flywheels
        cmd_fly = Float64MultiArray()
        cmd_fly.data = [100.0, 100.0]
        self.flywheel_pub.publish(cmd_fly)
        self.get_logger().info("Flywheels SPINNIG UP...")
        time.sleep(1.0)  # Wait for spin up

        # 2. Push Dart
        cmd_push = Float64MultiArray()
        cmd_push.data = [10.0]  # Velocity
        self.pusher_pub.publish(cmd_push)
        self.get_logger().info("Pusher ADVANCE")
        time.sleep(0.5)  # Wait for push

        # 3. Retract Pusher (Stop/Reverse?)
        # For continuous servo, 0.0 is stop.
        cmd_push.data = [0.0]
        self.pusher_pub.publish(cmd_push)
        self.get_logger().info("Pusher STOP")

        # 4. Spin down Flywheels
        cmd_fly.data = [0.0, 0.0]
        self.flywheel_pub.publish(cmd_fly)
        self.get_logger().info("Flywheels STOP")

        response.success = True
        response.message = "Dart fired!"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = NerfControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
