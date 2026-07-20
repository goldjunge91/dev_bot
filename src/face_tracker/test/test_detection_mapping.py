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
"""Pure Tests fuer face_tracker.detection_mapping."""

import pytest

from face_tracker.detection_mapping import face_location_to_bbox, score_for_name


def test_face_location_to_bbox_concrete_values():
    """(top=10, right=60, bottom=50, left=20) bei 100x200 Pixeln."""
    cx, cy, sx, sy = face_location_to_bbox((10, 60, 50, 20), rows=100, cols=200)
    assert cx == pytest.approx(0.2)  # (20+60)/2 / 200
    assert cy == pytest.approx(0.3)  # (10+50)/2 / 100
    assert sx == pytest.approx(0.2)  # (60-20) / 200
    assert sy == pytest.approx(0.4)  # (50-10) / 100


def test_face_location_to_bbox_full_frame():
    """Gesicht ueber das ganze Bild -> Zentrum 0.5/0.5, Groesse 1.0."""
    cx, cy, sx, sy = face_location_to_bbox((0, 200, 100, 0), rows=100, cols=200)
    assert (cx, cy, sx, sy) == pytest.approx((0.5, 0.5, 1.0, 1.0))


def test_face_location_to_bbox_values_in_unit_range():
    """Ergebnisse liegen fuer gueltige Pixelkoordinaten in [0, 1]."""
    for values in face_location_to_bbox((5, 90, 95, 10), rows=100, cols=100):
        assert 0.0 <= values <= 1.0


def test_score_for_name():
    """'unknown' -> 0.0, bekannte Namen -> 1.0."""
    assert score_for_name("unknown") == pytest.approx(0.0)
    assert score_for_name("alice") == pytest.approx(1.0)
