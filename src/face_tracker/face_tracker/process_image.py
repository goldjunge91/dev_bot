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

# Based on process_image.py by Tiziano Fiorenzani / Josh Newans
# Refactored to only contain face detection and recognition functions.

import cv2
import numpy as np
import face_recognition
import pickle
import os


def load_encodings(path):
    """
    Lädt gespeicherte Gesichts-Encodings aus einer .pkl-Datei.

    Gibt (known_encodings, known_names) zurück, oder ([], []) wenn Datei nicht existiert.
    """
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return [], []
    with open(expanded, "rb") as f:
        data = pickle.load(f)
    return data["encodings"], data["names"]


def find_and_identify_faces(
    image, known_encodings, known_names, tolerance=0.6, model="hog"
):
    """Erkennt Gesichter im Bild und identifiziert sie anhand gespeicherter Encodings."""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_image, model=model)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    face_names = []
    for encoding in face_encodings:
        name = "unknown"
        if len(known_encodings) > 0:
            matches = face_recognition.compare_faces(
                known_encodings, encoding, tolerance=tolerance
            )
            face_distances = face_recognition.face_distance(known_encodings, encoding)
            if True in matches:
                best_match_index = int(np.argmin(face_distances))
                if matches[best_match_index]:
                    name = known_names[best_match_index]
        face_names.append(name)

    out_image = draw_face_boxes(image.copy(), face_locations, face_names)
    return face_locations, face_names, out_image


def draw_face_boxes(image, face_locations, face_names):
    """Zeichnet Bounding Boxes und Namen auf das Bild."""
    color_map = {"unknown": (128, 128, 128)}
    default_colors = [
        (0, 255, 0),  # Grün   – Person 1
        (255, 128, 0),  # Orange – Person 2
        (0, 128, 255),  # Blau   – Person 3
    ]
    color_idx = 0

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        if name not in color_map:
            color_map[name] = default_colors[color_idx % len(default_colors)]
            color_idx += 1
        color = color_map[name]
        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
        cv2.rectangle(image, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            image,
            name,
            (left + 4, bottom - 8),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
    return image


def normalise_face(image, face_location):
    """Normalisiert eine Gesichtsposition auf [-1, 1] relativ zur Bildmitte."""
    rows = float(image.shape[0])
    cols = float(image.shape[1])
    center_x = 0.5 * cols
    center_y = 0.5 * rows
    top, right, bottom, left = face_location
    face_cx = (left + right) / 2.0
    face_cy = (top + bottom) / 2.0
    norm_x = (face_cx - center_x) / center_x
    norm_y = (face_cy - center_y) / center_y
    norm_size = float(right - left) / cols
    return norm_x, norm_y, norm_size
