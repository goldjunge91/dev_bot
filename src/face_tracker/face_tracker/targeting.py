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
Pure Ziel-Auswahl- und Feuer-Logik (kein rclpy).

Gemeinsame Logik von fire_at_face und follow_face, als testbare
Funktionen extrahiert. Detections sind duck-typed (vision_msgs
Detection2D oder Test-Doubles mit gleichen Attributen).
"""

from dataclasses import dataclass


def select_target(detections, target_person):
    """
    Waehlt die Ziel-Detection aus einer Liste aus.

    Mit target_person: erste Detection, deren class_id exakt passt
    (sonst None). Ohne: erste bekannte (nicht 'unknown'), Fallback
    die allererste Detection. Leere Liste -> None.
    """
    if not detections:
        return None

    if target_person:
        for det in detections:
            if det.results and det.results[0].hypothesis.class_id == target_person:
                return det
        return None

    for det in detections:
        if det.results and det.results[0].hypothesis.class_id != "unknown":
            return det
    return detections[0]


@dataclass(frozen=True)
class FireParams:
    """Parameter fuer die Feuer-Entscheidung."""

    threshold_x: float = 0.1
    threshold_y: float = 0.15
    min_size_thresh: float = 0.15
    cooldown_secs: float = 5.0
    camera_offset_x: float = 0.0
    camera_offset_y: float = 0.0


def evaluate_fire(center_x, center_y, size_x, now, last_fire_time, params):
    """
    Prueft Feuerbedingungen: (locked_on, cooldown_ready).

    locked_on: Ziel zentriert (strikt < Threshold in X und Y, relativ
    zum kameraversetzten Zentrum 0.5 + offset) und gross genug
    (strikt > min_size_thresh). cooldown_ready: Cooldown strikt
    abgelaufen.
    """
    target_center_x = 0.5 + params.camera_offset_x
    target_center_y = 0.5 + params.camera_offset_y

    offset_x = abs(center_x - target_center_x)
    offset_y = abs(center_y - target_center_y)

    is_centered = (offset_x < params.threshold_x) and (offset_y < params.threshold_y)
    is_close_enough = size_x > params.min_size_thresh
    is_cooldown_ready = (now - last_fire_time) > params.cooldown_secs

    return is_centered and is_close_enough, is_cooldown_ready
