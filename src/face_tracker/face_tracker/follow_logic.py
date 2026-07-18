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
Pure Verfolgungs-Logik von follow_face (kein rclpy).

Tiefpass-Filter, Detection-Normierung und Fahr-/Tilt-Kommando als
testbare Funktionen.
"""

from dataclasses import dataclass


def low_pass(previous, raw, f):
    """Exponentieller Tiefpass: previous * f + raw * (1 - f)."""
    return previous * f + raw * (1 - f)


def normalise_detection(cx, cy, size):
    """
    Normiert eine Detection fuer die Steuerung.

    cx [0,1] wird auf [-1,1] gemappt (0 = Bildmitte); cy und size
    bleiben im [0,1]-Format.
    """
    return (cx - 0.5) * 2.0, cy, size


@dataclass(frozen=True)
class FollowParams:
    """Parameter fuer das Verfolgungs-Kommando."""

    angular_chase_multiplier: float = 0.7
    forward_chase_speed: float = 0.1
    max_size_thresh: float = 0.3
    tilt_chase_multiplier: float = 0.1
    camera_offset_x: float = 0.0
    camera_offset_y: float = 0.0


def chase_command(target_val, target_y, target_dist, current_tilt, params):
    """
    Berechnet (linear_x, angular_z, neuer_tilt) fuer die Verfolgung.

    Vorwaerts nur solange das Gesicht kleiner als max_size_thresh ist;
    Rotation proportional zum X-Fehler (kameraversetzt); Tilt wird
    integriert und auf [0, 1] geklemmt.
    """
    linear_x = 0.0
    if target_dist < params.max_size_thresh:
        linear_x = params.forward_chase_speed

    offset_scaled_x = params.camera_offset_x * 2.0
    error_x = target_val - offset_scaled_x
    angular_z = -params.angular_chase_multiplier * error_x

    target_center_y = 0.5 + params.camera_offset_y
    error_y = target_center_y - target_y
    new_tilt = current_tilt + error_y * params.tilt_chase_multiplier
    new_tilt = max(0.0, min(1.0, new_tilt))

    return linear_x, angular_z, new_tilt
