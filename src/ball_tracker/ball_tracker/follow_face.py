# Copyright 2026 - Follow Face Node
# Basierend auf follow_ball.py von Josh Newans
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

# --- ALTE FOLLOW-BALL LOGIK (auskommentiert) ---
# Die ursprüngliche FollowBall-Node subscribed /detected_ball (Point)
# und publiziert /cmd_vel (Twist) um dem Ball zu folgen.
# Ersetzt durch FollowFace, die /face_detections (Detection2DArray) subscribed.
# ---

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from vision_msgs.msg import Detection2DArray
import time


class FollowFace(Node):
    def __init__(self):
        super().__init__("follow_face")

        # --- Subscriber & Publisher ---
        self.subscription = self.create_subscription(
            Detection2DArray, "/face_detections", self.listener_callback, 10
        )
        self.publisher_ = self.create_publisher(Twist, "/cmd_vel", 10)

        # --- Parameter ---
        self.declare_parameter("rcv_timeout_secs", 1.0)
        self.declare_parameter("angular_chase_multiplier", 0.7)
        self.declare_parameter("forward_chase_speed", 0.1)
        self.declare_parameter("search_angular_speed", 0.5)
        self.declare_parameter("max_size_thresh", 0.3)
        self.declare_parameter("filter_value", 0.9)
        self.declare_parameter("target_person", "")  # leer = erstes gefundenes Gesicht

        self.rcv_timeout_secs = (
            self.get_parameter("rcv_timeout_secs").get_parameter_value().double_value
        )
        self.angular_chase_multiplier = (
            self.get_parameter("angular_chase_multiplier")
            .get_parameter_value()
            .double_value
        )
        self.forward_chase_speed = (
            self.get_parameter("forward_chase_speed").get_parameter_value().double_value
        )
        self.search_angular_speed = (
            self.get_parameter("search_angular_speed")
            .get_parameter_value()
            .double_value
        )
        self.max_size_thresh = (
            self.get_parameter("max_size_thresh").get_parameter_value().double_value
        )
        self.filter_value = (
            self.get_parameter("filter_value").get_parameter_value().double_value
        )
        self.target_person = (
            self.get_parameter("target_person").get_parameter_value().string_value
        )

        # --- Zustand ---
        timer_period = 0.1  # Sekunden
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.target_val = 0.0  # normalisierte X-Position [-1, 1]
        self.target_dist = 0.0  # normalisierte Gesichtsgröße [0, 1]
        self.lastrcvtime = time.time() - 10000

        self.get_logger().info(
            f'FollowFace gestartet. Ziel-Person: "{self.target_person or "beliebig"}"'
        )

    def timer_callback(self):
        msg = Twist()
        if time.time() - self.lastrcvtime < self.rcv_timeout_secs:
            self.get_logger().info(
                f"Verfolge: x={self.target_val:.3f}, size={self.target_dist:.3f}"
            )
            if self.target_dist < self.max_size_thresh:
                msg.linear.x = self.forward_chase_speed
            msg.angular.z = -self.angular_chase_multiplier * self.target_val
        else:
            self.get_logger().info("Kein Gesicht – suche...")
            msg.angular.z = self.search_angular_speed
        self.publisher_.publish(msg)

    def listener_callback(self, msg: Detection2DArray):
        """Verarbeitet eingehende Gesichtserkennungs-Ergebnisse."""
        if not msg.detections:
            return

        target_det = None

        if self.target_person:
            # Bestimmte Person suchen
            for det in msg.detections:
                if (
                    det.results
                    and det.results[0].hypothesis.class_id == self.target_person
                ):
                    target_det = det
                    break
        else:
            # Erstes bekanntes Gesicht nehmen (kein 'unknown')
            for det in msg.detections:
                if det.results and det.results[0].hypothesis.class_id != "unknown":
                    target_det = det
                    break
            # Fallback: erstes Gesicht überhaupt
            if target_det is None and msg.detections:
                target_det = msg.detections[0]

        if target_det is None:
            return

        # bbox.center.x ist [0,1] → umrechnen auf [-1, 1] für Steuerung
        f = self.filter_value
        raw_x = (target_det.bbox.center.x - 0.5) * 2.0
        raw_size = target_det.bbox.size_x

        self.target_val = self.target_val * f + raw_x * (1 - f)
        self.target_dist = self.target_dist * f + raw_size * (1 - f)
        self.lastrcvtime = time.time()


def main(args=None):
    rclpy.init(args=args)
    follow_face = FollowFace()
    rclpy.spin(follow_face)
    follow_face.destroy_node()
    rclpy.shutdown()
