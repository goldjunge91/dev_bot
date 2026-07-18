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

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_srvs.srv import SetBool

from gubot_patrol.patrol_logic import (
    PatrolParams,
    PatrolPhase,
    advance_phase,
    command_for_phase,
    turn_duration_secs,
)


class PatrolNode(Node):
    """
    Dead-reckoning square patrol on cmd_vel_nav.

    Publishes at twist_mux's lowest priority so follow_face's
    cmd_vel_tracker automatically pre-empts it the moment a face
    locks on, and patrol resumes on its own once the tracker topic
    times out. This node has no awareness of face_detections by
    design — twist_mux already does that arbitration.
    """

    def __init__(self):
        super().__init__("patrol_node")

        self.declare_parameter("cmd_vel_topic", "cmd_vel_nav")
        self.declare_parameter("forward_speed", 0.15)
        self.declare_parameter("angular_speed", 0.6)
        self.declare_parameter("leg_duration_secs", 4.0)
        self.declare_parameter("num_legs", 4)
        self.declare_parameter("enabled", True)
        self.declare_parameter("control_rate_hz", 20.0)

        cmd_vel_topic = (
            self.get_parameter("cmd_vel_topic").get_parameter_value().string_value
        )
        self.forward_speed = (
            self.get_parameter("forward_speed").get_parameter_value().double_value
        )
        self.angular_speed = (
            self.get_parameter("angular_speed").get_parameter_value().double_value
        )
        self.leg_duration_secs = (
            self.get_parameter("leg_duration_secs").get_parameter_value().double_value
        )
        self.num_legs = (
            self.get_parameter("num_legs").get_parameter_value().integer_value
        )
        self.enabled = (
            self.get_parameter("enabled").get_parameter_value().bool_value
        )
        control_rate_hz = (
            self.get_parameter("control_rate_hz").get_parameter_value().double_value
        )

        # 90 degree turn at angular_speed, one turn per completed leg.
        self.turn_duration_secs = turn_duration_secs(self.angular_speed)

        self.cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.active_pub = self.create_publisher(Bool, "~/active", 10)
        self.set_enabled_srv = self.create_service(
            SetBool, "~/set_enabled", self._on_set_enabled
        )

        self._leg_index = 0
        self._turning = False
        self._phase_start = self.get_clock().now()

        period = 1.0 / control_rate_hz
        self.timer = self.create_timer(period, self._on_timer)

        self.get_logger().info(
            f"PatrolNode gestartet. topic={cmd_vel_topic}, "
            f"legs={self.num_legs}, forward={self.forward_speed} m/s, "
            f"enabled={self.enabled}"
        )

    def _on_set_enabled(self, request, response):
        self.enabled = request.data
        if not self.enabled:
            self.cmd_pub.publish(Twist())
        response.success = True
        response.message = "patrol enabled" if self.enabled else "patrol disabled"
        return response

    def _on_timer(self):
        self.active_pub.publish(Bool(data=self.enabled))
        if not self.enabled:
            return

        elapsed = (self.get_clock().now() - self._phase_start).nanoseconds / 1e9
        params = PatrolParams(
            forward_speed=self.forward_speed,
            angular_speed=self.angular_speed,
            leg_duration_secs=self.leg_duration_secs,
            num_legs=self.num_legs,
        )
        phase, phase_reset = advance_phase(
            PatrolPhase(leg_index=self._leg_index, turning=self._turning),
            elapsed,
            params,
        )
        if phase_reset:
            self._phase_start = self.get_clock().now()
        self._leg_index = phase.leg_index
        self._turning = phase.turning

        msg = Twist()
        msg.linear.x, msg.angular.z = command_for_phase(phase, params)
        self.cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
