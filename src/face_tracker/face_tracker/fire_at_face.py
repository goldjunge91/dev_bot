# Copyright 2026 Developer
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

# Triggers the Nerf Launcher when a face is locked on.

import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from std_srvs.srv import Trigger
import time


class FireAtFace(Node):
    def __init__(self):
        super().__init__("fire_at_face")

        # --- Parameters ---
        self.declare_parameter("target_person", "")  # Empty = any face
        self.declare_parameter(
            "fire_threshold_x", 0.1
        )  # Tolerance for X center (+/- 0.1)
        self.declare_parameter(
            "min_size_thresh", 0.15
        )  # Minimum size to fire (too far = don't fire)
        self.declare_parameter("cooldown_secs", 5.0)  # Wait between shots

        self.target_person = (
            self.get_parameter("target_person").get_parameter_value().string_value
        )
        self.threshold_x = (
            self.get_parameter("fire_threshold_x").get_parameter_value().double_value
        )
        self.declare_parameter("fire_threshold_y", 0.15)
        self.declare_parameter("camera_offset_x", 0.0)
        self.declare_parameter("camera_offset_y", 0.0)

        self.threshold_y = (
            self.get_parameter("fire_threshold_y").get_parameter_value().double_value
        )
        self.camera_offset_x = (
            self.get_parameter("camera_offset_x").get_parameter_value().double_value
        )
        self.camera_offset_y = (
            self.get_parameter("camera_offset_y").get_parameter_value().double_value
        )
        self.min_size_thresh = (
            self.get_parameter("min_size_thresh").get_parameter_value().double_value
        )
        self.cooldown_secs = (
            self.get_parameter("cooldown_secs").get_parameter_value().double_value
        )

        # --- Service Client ---
        self.fire_client = self.create_client(Trigger, "/nerf/fire")

        # --- Subscriber ---
        self.subscription = self.create_subscription(
            Detection2DArray, "/face_detections", self.listener_callback, 10
        )

        self.last_fire_time = 0.0
        self.get_logger().info(
            f"FireAtFace started. Target: '{self.target_person or 'ANY'}'. Cooldown: {self.cooldown_secs}s"  # noqa: E501
        )

    def listener_callback(self, msg: Detection2DArray):
        if not msg.detections:
            return

        target_det = None

        # Find target
        if self.target_person:
            for det in msg.detections:
                if (
                    det.results
                    and det.results[0].hypothesis.class_id == self.target_person
                ):
                    target_det = det
                    break
        else:
            # Any face
            for det in msg.detections:
                if det.results and det.results[0].hypothesis.class_id != "unknown":
                    target_det = det
                    break
            if target_det is None and msg.detections:
                target_det = msg.detections[0]

        if target_det is None:
            return

        # bbox.center.position.x/y is 0.0 to 1.0.
        # Mit Camera Offset vergleichen (Zentrum der Kamera ist 0.5)
        target_center_x = 0.5 + self.camera_offset_x
        target_center_y = 0.5 + self.camera_offset_y

        center_x = target_det.bbox.center.position.x
        center_y = target_det.bbox.center.position.y

        offset_x = abs(center_x - target_center_x)
        offset_y = abs(center_y - target_center_y)

        size_x = target_det.bbox.size_x

        # Logic:
        # 1. Subject is centered in X AND Y ?
        # 2. Subject is close enough ?
        # 3. Cooldown expired ?

        is_centered = (offset_x < self.threshold_x) and (offset_y < self.threshold_y)
        is_close_enough = size_x > self.min_size_thresh
        is_cooldown_ready = (time.time() - self.last_fire_time) > self.cooldown_secs

        if is_centered and is_close_enough:
            if is_cooldown_ready:
                self.get_logger().warn(
                    f"LOCKED ON! Firing at {target_det.results[0].hypothesis.class_id if target_det.results else 'Generic'}"  # noqa: E501
                )
                self.trigger_fire()
            else:
                # pass
                # self.get_logger().info(f"Locked on... waiting for cooldown ({self.cooldown_secs - (time.time() - self.last_fire_time):.1f}s)")  # noqa: E501
                remaining = self.cooldown_secs - (time.time() - self.last_fire_time)
                self.get_logger().info(
                    f"Locked on... waiting for cooldown ({remaining:.1f}s)",
                    throttle_duration_sec=2.0,
                )

    def trigger_fire(self):
        if not self.fire_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().error("Service /nerf/fire not available!")
            return

        req = Trigger.Request()
        self.last_fire_time = time.time()  # Reset cooldown immediately

        future = self.fire_client.call_async(req)
        future.add_done_callback(self.fire_response_callback)

    def fire_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info("SHOT FIRED SUCCESSFULLY! 💥")
            else:
                self.get_logger().warn(f"Shot failed: {response.message}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = FireAtFace()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
