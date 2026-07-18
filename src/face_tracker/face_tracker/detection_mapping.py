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
"""
Pure Abbildung von Gesichtspositionen auf Bounding-Box-Werte.

Rechnet face_recognition-Pixelkoordinaten in normierte Werte um
(kein rclpy, kein vision_msgs).
"""


def face_location_to_bbox(face_location, rows, cols):
    """
    Normiert eine Gesichtsposition auf [0, 1].

    (top, right, bottom, left) in Pixeln -> (cx, cy, size_x, size_y).
    """
    top, right, bottom, left = face_location
    cx = (left + right) / 2.0
    cy = (top + bottom) / 2.0
    return (
        cx / cols,
        cy / rows,
        float(right - left) / cols,
        float(bottom - top) / rows,
    )


def score_for_name(name):
    """Score fuer eine erkannte Person: 0.0 fuer 'unknown', sonst 1.0."""
    return 0.0 if name == "unknown" else 1.0
