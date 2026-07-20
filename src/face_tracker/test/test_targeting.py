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
"""Pure Tests fuer face_tracker.targeting (select_target + evaluate_fire)."""

from conftest import make_detection

from face_tracker.targeting import FireParams, evaluate_fire, select_target

# --- select_target ---


def test_select_target_empty_list_returns_none():
    """Leere Detection-Liste -> None."""
    assert select_target([], "") is None
    assert select_target([], "alice") is None


def test_select_target_named_person_found():
    """Benannte Person wird gefunden, auch wenn nicht erste."""
    dets = [make_detection("bob"), make_detection("alice")]
    assert select_target(dets, "alice") is dets[1]


def test_select_target_named_person_missing_returns_none():
    """Benannte Person fehlt -> None (kein Fallback)."""
    dets = [make_detection("bob"), make_detection("unknown")]
    assert select_target(dets, "alice") is None


def test_select_target_prefers_known_over_unknown():
    """Ohne Zielperson: erstes bekanntes Gesicht schlaegt 'unknown'."""
    dets = [make_detection("unknown"), make_detection("bob")]
    assert select_target(dets, "") is dets[1]


def test_select_target_all_unknown_falls_back_to_first():
    """Nur 'unknown'-Gesichter -> allererste Detection."""
    dets = [make_detection("unknown"), make_detection("unknown")]
    assert select_target(dets, "") is dets[0]


def test_select_target_skips_detections_without_results():
    """Detections ohne results werden bei der Suche uebersprungen."""
    dets = [make_detection("x", with_results=False), make_detection("bob")]
    assert select_target(dets, "") is dets[1]
    assert select_target(dets, "bob") is dets[1]


# --- evaluate_fire ---

PARAMS = FireParams(
    threshold_x=0.1,
    threshold_y=0.15,
    min_size_thresh=0.15,
    cooldown_secs=5.0,
)


def test_evaluate_fire_locked_and_ready():
    """Zentriert, gross genug, Cooldown abgelaufen -> (True, True)."""
    locked, ready = evaluate_fire(0.5, 0.5, 0.2, 100.0, 0.0, PARAMS)
    assert locked is True
    assert ready is True


def test_evaluate_fire_off_center_x_blocks():
    """X-Offset ueber dem Threshold sperrt; darunter nicht."""
    locked, _ = evaluate_fire(0.61, 0.5, 0.2, 100.0, 0.0, PARAMS)
    assert locked is False
    locked, _ = evaluate_fire(0.55, 0.5, 0.2, 100.0, 0.0, PARAMS)
    assert locked is True


def test_evaluate_fire_off_center_y_blocks():
    """Y-Offset ueber dem Threshold sperrt; darunter nicht."""
    locked, _ = evaluate_fire(0.5, 0.66, 0.2, 100.0, 0.0, PARAMS)
    assert locked is False
    locked, _ = evaluate_fire(0.5, 0.6, 0.2, 100.0, 0.0, PARAMS)
    assert locked is True


def test_evaluate_fire_too_small_strict_boundary():
    """Groesse genau am Threshold sperrt (strikt >)."""
    locked, _ = evaluate_fire(0.5, 0.5, 0.15, 100.0, 0.0, PARAMS)
    assert locked is False
    locked, _ = evaluate_fire(0.5, 0.5, 0.151, 100.0, 0.0, PARAMS)
    assert locked is True


def test_evaluate_fire_cooldown_boundary():
    """Cooldown genau erreicht -> nicht ready; knapp darueber -> ready."""
    _, ready = evaluate_fire(0.5, 0.5, 0.2, 105.0, 100.0, PARAMS)
    assert ready is False
    _, ready = evaluate_fire(0.5, 0.5, 0.2, 105.01, 100.0, PARAMS)
    assert ready is True


def test_evaluate_fire_camera_offset_shifts_target_center():
    """camera_offset verschiebt das Zielzentrum."""
    offset_params = FireParams(camera_offset_x=0.2, camera_offset_y=-0.1)
    # Bildmitte 0.5/0.5 ist jetzt off-center relativ zu 0.7/0.4.
    locked, _ = evaluate_fire(0.5, 0.5, 0.2, 100.0, 0.0, offset_params)
    assert locked is False
    locked, _ = evaluate_fire(0.7, 0.4, 0.2, 100.0, 0.0, offset_params)
    assert locked is True
