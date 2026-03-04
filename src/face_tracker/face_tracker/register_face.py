# Copyright 2026 - Face Registration Node
#
# Registriert Gesichter für die face_recognition Bibliothek.
# Nimmt Fotos per Kamera auf, berechnet Encodings und speichert sie.
#
# Aufruf:
#   ros2 run face_tracker register_face --ros-args -p person_name:=marco
#   ros2 run face_tracker register_face --ros-args -p person_name:=schatz -p num_samples:=40

import rclpy
from rclpy.node import Node
import cv2
import face_recognition
import pickle
import os
import time


class RegisterFace(Node):
    def __init__(self):
        super().__init__("register_face")

        # --- Parameter ---
        self.declare_parameter("person_name", "")
        self.declare_parameter("num_samples", 30)
        self.declare_parameter("encodings_path", "~/.ros/face_detector/encodings.pkl")
        self.declare_parameter("camera_index", 0)
        self.declare_parameter("capture_delay_ms", 200)

        self.person_name = (
            self.get_parameter("person_name").get_parameter_value().string_value
        )
        self.num_samples = (
            self.get_parameter("num_samples").get_parameter_value().integer_value
        )
        self.encodings_path = os.path.expanduser(
            self.get_parameter("encodings_path").get_parameter_value().string_value
        )
        self.camera_index = (
            self.get_parameter("camera_index").get_parameter_value().integer_value
        )
        self.capture_delay = (
            self.get_parameter("capture_delay_ms").get_parameter_value().integer_value
            / 1000.0
        )

        if not self.person_name:
            self.get_logger().error(
                "Kein person_name angegeben!\n"
                "Aufruf: ros2 run face_tracker register_face --ros-args -p person_name:=<name>"
            )
            return

        self.get_logger().info(
            f'Registriere Person: "{self.person_name}" | '
            f"{self.num_samples} Samples | "
            f"Speicherpfad: {self.encodings_path}"
        )

        self.run_registration()

    def run_registration(self):
        """Öffnet Kamera, nimmt Bilder auf und speichert Encodings."""
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.get_logger().error(
                f"Kamera {self.camera_index} konnte nicht geöffnet werden!"
            )
            return

        self.get_logger().info(
            "Kamera geöffnet. Bitte ins Bild schauen.\n"
            "Drücke LEERTASTE um ein Sample aufzunehmen, Q zum Abbrechen."
        )

        collected_encodings = []
        sample_count = 0

        while sample_count < self.num_samples and rclpy.ok():
            ret, frame = cap.read()
            if not ret:
                self.get_logger().warn("Kein Bild von Kamera erhalten.")
                continue

            display = frame.copy()
            cv2.putText(
                display,
                f"Person: {self.person_name} | Samples: {sample_count}/{self.num_samples}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                display,
                "LEERTASTE: Sample aufnehmen | Q: Abbrechen",
                (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )
            cv2.imshow("Gesicht registrieren", display)

            key = cv2.waitKey(30) & 0xFF

            if key == ord("q") or key == 27:
                self.get_logger().info("Registrierung abgebrochen.")
                break

            elif key == ord(" "):
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)

                if not face_locations:
                    self.get_logger().warn(
                        "Kein Gesicht im Bild erkannt – bitte neu positionieren."
                    )
                    continue

                if len(face_locations) > 1:
                    self.get_logger().warn(
                        f"{len(face_locations)} Gesichter erkannt – bitte nur eine Person im Bild."
                    )
                    continue

                encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if encodings:
                    collected_encodings.append(encodings[0])
                    sample_count += 1
                    self.get_logger().info(
                        f"Sample {sample_count}/{self.num_samples} aufgenommen."
                    )

                    top, right, bottom, left = face_locations[0]
                    cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 3)
                    cv2.imshow("Gesicht registrieren", display)
                    cv2.waitKey(300)
                    time.sleep(self.capture_delay)

        cap.release()
        cv2.destroyAllWindows()

        if not collected_encodings:
            self.get_logger().error("Keine Encodings gesammelt – nichts gespeichert.")
            return

        # Bestehende Encodings laden und neue hinzufügen
        existing_encodings = []
        existing_names = []
        if os.path.exists(self.encodings_path):
            with open(self.encodings_path, "rb") as f:
                data = pickle.load(f)
                existing_encodings = data.get("encodings", [])
                existing_names = data.get("names", [])

        all_encodings = existing_encodings + collected_encodings
        all_names = existing_names + [self.person_name] * len(collected_encodings)

        os.makedirs(os.path.dirname(self.encodings_path), exist_ok=True)
        with open(self.encodings_path, "wb") as f:
            pickle.dump({"encodings": all_encodings, "names": all_names}, f)

        self.get_logger().info(
            f'Erfolgreich gespeichert: {len(collected_encodings)} Encodings für "{self.person_name}"\n'
            f"Alle registrierten Personen: {list(set(all_names))}"
        )


def main(args=None):
    rclpy.init(args=args)
    register_face = RegisterFace()
    register_face.destroy_node()
    rclpy.shutdown()
