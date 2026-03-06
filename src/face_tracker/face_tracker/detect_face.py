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

# Basierend auf detect_ball.py von Josh Newans
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from vision_msgs.msg import (
    Detection2DArray,
    Detection2D,
    ObjectHypothesisWithPose,
    BoundingBox2D,
)

import face_tracker.process_image as proc


class DetectFace(Node):
    def __init__(self):
        super().__init__("detect_face")

        self.get_logger().info("Face Detector gestartet – warte auf Bilder...")

        # --- Subscriber & Publisher ---
        self.image_sub = self.create_subscription(
            Image,
            "/image_in",
            self.callback,
            rclpy.qos.QoSPresetProfiles.SENSOR_DATA.value,
        )
        self.image_out_pub = self.create_publisher(Image, "/image_out", 1)
        self.detections_pub = self.create_publisher(
            Detection2DArray, "/face_detections", 1
        )

        # --- Parameter ---
        self.declare_parameter("encodings_path", "~/.ros/face_detector/encodings.pkl")
        self.declare_parameter("tolerance", 0.6)
        self.declare_parameter("model", "hog")  # 'hog' oder 'cnn'

        encodings_path = (
            self.get_parameter("encodings_path").get_parameter_value().string_value
        )
        self.tolerance = (
            self.get_parameter("tolerance").get_parameter_value().double_value
        )
        self.model = self.get_parameter("model").get_parameter_value().string_value

        # --- Encodings laden ---
        self.known_encodings, self.known_names = proc.load_encodings(encodings_path)
        if len(self.known_names) == 0:
            self.get_logger().warn(
                f"Keine Gesichts-Encodings gefunden unter: {encodings_path}\n"
                "Bitte zuerst encode_faces.py ausführen."
            )
        else:
            self.get_logger().info(f"Encodings geladen: {list(set(self.known_names))}")

        self.bridge = CvBridge()

    def callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge Fehler: {e}")
            return

        try:
            face_locations, face_names, out_image = proc.find_and_identify_faces(
                cv_image,
                self.known_encodings,
                self.known_names,
                tolerance=self.tolerance,
                model=self.model,
            )

            # --- Annotiertes Bild publizieren ---
            img_msg = self.bridge.cv2_to_imgmsg(out_image, "bgr8")
            img_msg.header = data.header
            self.image_out_pub.publish(img_msg)

            # --- Detection2DArray aufbauen ---
            det_array = Detection2DArray()
            det_array.header = data.header

            rows = float(cv_image.shape[0])
            cols = float(cv_image.shape[1])

            for (top, right, bottom, left), name in zip(face_locations, face_names):
                det = Detection2D()
                det.header = data.header

                # Bounding Box (Mittelpunkt normalisiert auf [0,1])
                bbox = BoundingBox2D()
                cx = (left + right) / 2.0
                cy = (top + bottom) / 2.0

                # Center ist ein vision_msgs/Pose2D, hat 'position' (Point2D) und 'theta'
                bbox.center.position.x = cx / cols
                bbox.center.position.y = cy / rows
                bbox.center.theta = 0.0

                bbox.size_x = float(right - left) / cols
                bbox.size_y = float(bottom - top) / rows
                det.bbox = bbox

                # Klasse (Personenname) + Score
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = name
                hyp.hypothesis.score = 0.0 if name == "unknown" else 1.0
                det.results.append(hyp)

                det_array.detections.append(det)

                self.get_logger().debug(
                    f"Gesicht erkannt: {name} @ ({cx:.0f}, {cy:.0f})"
                )

            self.detections_pub.publish(det_array)

        except Exception as e:
            self.get_logger().error(f"Fehler bei Gesichtserkennung: {e}")


def main(args=None):
    rclpy.init(args=args)
    detect_face = DetectFace()
    rclpy.spin(detect_face)
    detect_face.destroy_node()
    rclpy.shutdown()
