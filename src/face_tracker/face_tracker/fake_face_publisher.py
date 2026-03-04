#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
import math


class FakeFacePublisher(Node):
    def __init__(self):
        super().__init__("fake_face_publisher")
        self.publisher_ = self.create_publisher(
            Detection2DArray, "/face_detections", 10
        )
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.start_time = self.get_clock().now()
        self.get_logger().info(
            "Fake Face Publisher gestartet. Sende Test-Koordinaten..."
        )
        self.get_logger().info(
            "Hinweis: Alle 10 Sekunden wird das Gesicht fuer 2 Sekunden zentriert (LOCK ON)."
        )

    def timer_callback(self):
        now = self.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9

        # Alle 10 Sekunden ein "Lock On" Event erzwingen
        cycle = elapsed % 10.0

        if cycle < 2.0:
            # Zentriert und groß genug zum Feuern
            x = 0.5
            y = 0.5
            size = 0.25
        else:
            # Kreisende Bewegung (Suche)
            x = 0.5 + 0.3 * math.sin(elapsed * 0.5)
            y = 0.5 + 0.2 * math.cos(elapsed * 0.3)
            size = 0.15

        msg = Detection2DArray()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = "camera_link_optical"

        detection = Detection2D()
        detection.bbox.center.position.x = x
        detection.bbox.center.position.y = y
        detection.bbox.size_x = size
        detection.bbox.size_y = size

        hyp = ObjectHypothesisWithPose()
        hyp.hypothesis.class_id = "test_face"
        hyp.hypothesis.score = 0.95
        detection.results.append(hyp)

        msg.detections.append(detection)
        self.publisher_.publish(msg)


def main(args=None):
    if not rclpy.ok():
        rclpy.init(args=args)
    node = FakeFacePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
