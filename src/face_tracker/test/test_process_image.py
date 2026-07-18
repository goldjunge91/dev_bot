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
"""Tests fuer face_tracker.process_image (face_recognition gemockt)."""

import pickle

import numpy as np
import pytest

import face_tracker.process_image as proc


def _blank_image(rows=60, cols=80):
    """Erzeugt ein schwarzes BGR-Testbild."""
    return np.zeros((rows, cols, 3), dtype=np.uint8)


# --- load_encodings ---


def test_load_encodings_missing_file(tmp_path):
    """Fehlende Datei -> ([], [])."""
    encodings, names = proc.load_encodings(str(tmp_path / "nope.pkl"))
    assert encodings == []
    assert names == []


def test_load_encodings_roundtrip(tmp_path):
    """Gespeicherte Encodings werden korrekt zurueckgelesen."""
    path = tmp_path / "enc.pkl"
    data = {"encodings": [[0.1, 0.2]], "names": ["alice"]}
    with open(path, "wb") as f:
        pickle.dump(data, f)
    encodings, names = proc.load_encodings(str(path))
    assert encodings == [[0.1, 0.2]]
    assert names == ["alice"]


def test_load_encodings_expands_user(monkeypatch, tmp_path):
    """~ im Pfad wird expandiert."""
    path = tmp_path / "enc.pkl"
    with open(path, "wb") as f:
        pickle.dump({"encodings": [], "names": []}, f)
    monkeypatch.setenv("HOME", str(tmp_path))
    encodings, names = proc.load_encodings("~/enc.pkl")
    assert encodings == []
    assert names == []


# --- find_and_identify_faces ---


def test_find_faces_no_locations(monkeypatch):
    """Keine Gesichter -> leere Listen, Bild unveraendert gross."""
    monkeypatch.setattr(proc.face_recognition, "face_locations", lambda *a, **k: [])
    monkeypatch.setattr(proc.face_recognition, "face_encodings", lambda *a, **k: [])
    locations, names, out = proc.find_and_identify_faces(_blank_image(), [], [])
    assert locations == []
    assert names == []
    assert out.shape == _blank_image().shape


def test_find_faces_unknown_without_known_encodings(monkeypatch):
    """Ohne bekannte Encodings heisst jedes Gesicht 'unknown'."""
    monkeypatch.setattr(
        proc.face_recognition, "face_locations", lambda *a, **k: [(5, 30, 25, 10)]
    )
    monkeypatch.setattr(
        proc.face_recognition, "face_encodings", lambda *a, **k: [np.zeros(128)]
    )
    _, names, _ = proc.find_and_identify_faces(_blank_image(), [], [])
    assert names == ["unknown"]


def test_find_faces_best_match_via_argmin(monkeypatch):
    """Bei mehreren Matches gewinnt die kleinste face_distance."""
    monkeypatch.setattr(
        proc.face_recognition, "face_locations", lambda *a, **k: [(5, 30, 25, 10)]
    )
    monkeypatch.setattr(
        proc.face_recognition, "face_encodings", lambda *a, **k: [np.zeros(128)]
    )
    monkeypatch.setattr(
        proc.face_recognition, "compare_faces", lambda *a, **k: [True, True]
    )
    monkeypatch.setattr(
        proc.face_recognition,
        "face_distance",
        lambda *a, **k: np.array([0.5, 0.2]),
    )
    _, names, _ = proc.find_and_identify_faces(
        _blank_image(), [np.zeros(128), np.zeros(128)], ["alice", "bob"]
    )
    assert names == ["bob"]


def test_find_faces_no_match_stays_unknown(monkeypatch):
    """compare_faces ohne True -> 'unknown' trotz bekannter Encodings."""
    monkeypatch.setattr(
        proc.face_recognition, "face_locations", lambda *a, **k: [(5, 30, 25, 10)]
    )
    monkeypatch.setattr(
        proc.face_recognition, "face_encodings", lambda *a, **k: [np.zeros(128)]
    )
    monkeypatch.setattr(
        proc.face_recognition, "compare_faces", lambda *a, **k: [False]
    )
    monkeypatch.setattr(
        proc.face_recognition, "face_distance", lambda *a, **k: np.array([0.9])
    )
    _, names, _ = proc.find_and_identify_faces(
        _blank_image(), [np.zeros(128)], ["alice"]
    )
    assert names == ["unknown"]


# --- draw_face_boxes / normalise_face ---


def test_draw_face_boxes_reuses_color_per_name():
    """Gleicher Name -> gleiche Farbe; Bild wird gezeichnet (nicht schwarz)."""
    image = _blank_image()
    out = proc.draw_face_boxes(
        image, [(5, 30, 25, 10), (5, 70, 25, 50)], ["alice", "alice"]
    )
    assert out.sum() > 0


def test_normalise_face_center_and_size():
    """Gesicht in der Bildmitte -> norm_x == norm_y == 0."""
    image = _blank_image(rows=100, cols=200)
    # Zentrum bei (100, 50): left=80, right=120, top=30, bottom=70
    norm_x, norm_y, norm_size = proc.normalise_face(image, (30, 120, 70, 80))
    assert norm_x == pytest.approx(0.0)
    assert norm_y == pytest.approx(0.0)
    assert norm_size == pytest.approx(40.0 / 200.0)
