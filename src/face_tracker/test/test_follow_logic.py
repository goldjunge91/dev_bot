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
"""Pure Tests fuer face_tracker.follow_logic."""

import pytest

from face_tracker.follow_logic import (
    FollowParams,
    chase_command,
    low_pass,
    normalise_detection,
)

PARAMS = FollowParams(
    angular_chase_multiplier=0.7,
    forward_chase_speed=0.1,
    max_size_thresh=0.3,
    tilt_chase_multiplier=0.1,
)


def test_low_pass_extremes():
    """f=1 haelt den alten Wert, f=0 uebernimmt den neuen."""
    assert low_pass(2.0, 10.0, 1.0) == pytest.approx(2.0)
    assert low_pass(2.0, 10.0, 0.0) == pytest.approx(10.0)


def test_low_pass_blend():
    """f=0.9 mischt 90 % alt und 10 % neu."""
    assert low_pass(0.0, 1.0, 0.9) == pytest.approx(0.1)


def test_normalise_detection_center():
    """Bildmitte cx=0.5 wird zu 0.0; y und size unveraendert."""
    x, y, size = normalise_detection(0.5, 0.25, 0.2)
    assert x == pytest.approx(0.0)
    assert y == pytest.approx(0.25)
    assert size == pytest.approx(0.2)


def test_normalise_detection_edges():
    """cx=0 -> -1, cx=1 -> +1."""
    assert normalise_detection(0.0, 0.5, 0.1)[0] == pytest.approx(-1.0)
    assert normalise_detection(1.0, 0.5, 0.1)[0] == pytest.approx(1.0)


def test_chase_command_steering_sign():
    """Ziel rechts (target_val > 0) -> Drehung nach rechts (negativ)."""
    _, angular_z, _ = chase_command(0.5, 0.5, 0.1, 0.5, PARAMS)
    assert angular_z == pytest.approx(-0.35)
    _, angular_z, _ = chase_command(-0.5, 0.5, 0.1, 0.5, PARAMS)
    assert angular_z == pytest.approx(0.35)


def test_chase_command_forward_until_close():
    """Vorwaerts nur solange Gesicht kleiner als max_size_thresh."""
    linear_x, _, _ = chase_command(0.0, 0.5, 0.1, 0.5, PARAMS)
    assert linear_x == pytest.approx(0.1)
    linear_x, _, _ = chase_command(0.0, 0.5, 0.3, 0.5, PARAMS)
    assert linear_x == pytest.approx(0.0)


def test_chase_command_tilt_integrates_error():
    """Gesicht oben (target_y < 0.5) -> Tilt steigt."""
    _, _, tilt = chase_command(0.0, 0.3, 0.1, 0.5, PARAMS)
    assert tilt == pytest.approx(0.5 + 0.2 * 0.1)
    _, _, tilt = chase_command(0.0, 0.7, 0.1, 0.5, PARAMS)
    assert tilt == pytest.approx(0.5 - 0.2 * 0.1)


def test_chase_command_tilt_clamped():
    """Tilt bleibt in [0, 1] geklemmt."""
    _, _, tilt = chase_command(0.0, 0.0, 0.1, 0.99, PARAMS)
    assert tilt <= 1.0
    _, _, tilt = chase_command(0.0, 1.0, 0.1, 0.01, PARAMS)
    assert tilt >= 0.0


def test_chase_command_camera_offset_x_shifts_zero_point():
    """camera_offset_x verschiebt den Nullpunkt der Rotation."""
    params = FollowParams(
        angular_chase_multiplier=0.7,
        forward_chase_speed=0.1,
        max_size_thresh=0.3,
        tilt_chase_multiplier=0.1,
        camera_offset_x=0.1,
    )
    # target_val == offset * 2 -> kein Drehfehler
    _, angular_z, _ = chase_command(0.2, 0.5, 0.1, 0.5, params)
    assert angular_z == pytest.approx(0.0)


def test_chase_command_camera_offset_y_shifts_tilt_center():
    """camera_offset_y verschiebt das Tilt-Zielzentrum."""
    params = FollowParams(
        angular_chase_multiplier=0.7,
        forward_chase_speed=0.1,
        max_size_thresh=0.3,
        tilt_chase_multiplier=0.1,
        camera_offset_y=0.1,
    )
    # target_y == 0.6 == 0.5 + offset -> kein Tilt-Fehler
    _, _, tilt = chase_command(0.0, 0.6, 0.1, 0.5, params)
    assert tilt == pytest.approx(0.5)
