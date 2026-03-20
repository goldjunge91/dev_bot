#!/usr/bin/env python3
"""
Kompatibilitaets-Bridge fuer alte Nerf-Teleop-Topicnamen.

Alt (nerf_teleop.py):
  - /shooter_controller/commands
  - /tilt_controller/commands

Neu (gubot_one ros2_control):
  - /pusher_controller/commands
  - /trigger_controller/commands
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray


class NerfTopicCompat(Node):
    def __init__(self):
        super().__init__("nerf_topic_compat")

        self.pub_pusher = self.create_publisher(
            Float64MultiArray,
            "/pusher_controller/commands",
            10,
        )
        self.pub_trigger = self.create_publisher(
            Float64MultiArray,
            "/trigger_controller/commands",
            10,
        )

        self.sub_shooter = self.create_subscription(
            Float64MultiArray,
            "/shooter_controller/commands",
            self._on_shooter,
            10,
        )
        self.sub_tilt = self.create_subscription(
            Float64MultiArray,
            "/tilt_controller/commands",
            self._on_tilt,
            10,
        )

        self.get_logger().info(
            "Nerf topic compatibility active: "
            "/shooter_controller/commands -> /pusher_controller/commands, "
            "/tilt_controller/commands -> /trigger_controller/commands"
        )

    def _on_shooter(self, msg: Float64MultiArray) -> None:
        out = Float64MultiArray()
        out.data = [float(x) for x in msg.data]
        self.pub_pusher.publish(out)

    def _on_tilt(self, msg: Float64MultiArray) -> None:
        out = Float64MultiArray()
        out.data = [float(x) for x in msg.data]
        self.pub_trigger.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = NerfTopicCompat()
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
