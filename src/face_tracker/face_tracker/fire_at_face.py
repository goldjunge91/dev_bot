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

# Triggers the Nerf Launcher when a face is locked on.

import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from std_srvs.srv import Trigger
import time

from face_tracker.targeting import FireParams, evaluate_fire, select_target


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
            f"FireAtFace started. Target: '{self.target_person or 'ANY'}'. "
            f"Cooldown: {self.cooldown_secs}s"
        )

    def listener_callback(self, msg: Detection2DArray):
        if not msg.detections:
            return

        target_det = select_target(msg.detections, self.target_person)
        if target_det is None:
            return

        params = FireParams(
            threshold_x=self.threshold_x,
            threshold_y=self.threshold_y,
            min_size_thresh=self.min_size_thresh,
            cooldown_secs=self.cooldown_secs,
            camera_offset_x=self.camera_offset_x,
            camera_offset_y=self.camera_offset_y,
        )
        locked_on, is_cooldown_ready = evaluate_fire(
            target_det.bbox.center.position.x,
            target_det.bbox.center.position.y,
            target_det.bbox.size_x,
            time.time(),
            self.last_fire_time,
            params,
        )

        if locked_on:
            if is_cooldown_ready:
                target_id = (
                    target_det.results[0].hypothesis.class_id
                    if target_det.results else 'Generic'
                )
                self.get_logger().warn(f"LOCKED ON! Firing at {target_id}")
                self.trigger_fire()
            else:
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
