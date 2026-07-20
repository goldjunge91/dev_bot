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
Gemeinsame Test-Hilfen fuer face_tracker.

Stellt einen face_recognition-Stub bereit, falls die Bibliothek nicht
installiert ist, sowie ein leichtgewichtiges Detection-Double.
"""

import sys
import types
from types import SimpleNamespace


def _install_face_recognition_stub():
    """Installiert einen minimalen face_recognition-Stub in sys.modules."""
    stub = types.ModuleType("face_recognition")
    stub.face_locations = lambda *a, **k: []
    stub.face_encodings = lambda *a, **k: []
    stub.compare_faces = lambda *a, **k: []
    stub.face_distance = lambda *a, **k: []
    sys.modules["face_recognition"] = stub


try:
    import face_recognition  # noqa: F401
except ImportError:
    _install_face_recognition_stub()


def make_detection(class_id, cx=0.5, cy=0.5, size=0.2, with_results=True):
    """Baut ein duck-typed Detection2D-Double fuer die pure Logik."""
    results = []
    if with_results:
        results = [SimpleNamespace(hypothesis=SimpleNamespace(class_id=class_id))]
    return SimpleNamespace(
        results=results,
        bbox=SimpleNamespace(
            center=SimpleNamespace(position=SimpleNamespace(x=cx, y=cy)),
            size_x=size,
            size_y=size,
        ),
    )
