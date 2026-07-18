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
rclpy-Tests fuer DetectFace.

Der Bild-Callback wird direkt mit CvBridge-Images aufgerufen;
find_and_identify_faces ist gemockt, die Publisher werden abgefangen.
"""

import numpy as np
import pytest
import rclpy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

import face_tracker.process_image as proc
from face_tracker.detect_face import DetectFace


@pytest.fixture(scope="module")
def rclpy_ctx():
    """ROS-Kontext einmal pro Modul."""
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def node(rclpy_ctx):
    """DetectFace-Node mit abgefangenen Publishern."""
    n = DetectFace()
    n.published_detections = []
    n.published_images = []
    n.detections_pub.publish = n.published_detections.append
    n.image_out_pub.publish = n.published_images.append
    yield n
    n.destroy_node()


def _image_msg(rows=100, cols=200):
    """Erzeugt eine echte sensor_msgs/Image via CvBridge."""
    frame = np.zeros((rows, cols, 3), dtype=np.uint8)
    return CvBridge().cv2_to_imgmsg(frame, "bgr8")


def test_callback_publishes_normalised_detection(node, monkeypatch):
    """Ein Gesicht -> normierte bbox + class_id + Score 1.0."""
    monkeypatch.setattr(
        proc,
        "find_and_identify_faces",
        lambda image, *a, **k: ([(10, 60, 50, 20)], ["alice"], image),
    )
    node.callback(_image_msg())
    assert len(node.published_detections) == 1
    det = node.published_detections[0].detections[0]
    assert det.bbox.center.position.x == pytest.approx(0.2)
    assert det.bbox.center.position.y == pytest.approx(0.3)
    assert det.bbox.size_x == pytest.approx(0.2)
    assert det.bbox.size_y == pytest.approx(0.4)
    assert det.results[0].hypothesis.class_id == "alice"
    assert det.results[0].hypothesis.score == pytest.approx(1.0)
    assert len(node.published_images) == 1


def test_callback_unknown_face_scores_zero(node, monkeypatch):
    """'unknown' -> Score 0.0."""
    monkeypatch.setattr(
        proc,
        "find_and_identify_faces",
        lambda image, *a, **k: ([(10, 60, 50, 20)], ["unknown"], image),
    )
    node.callback(_image_msg())
    hyp = node.published_detections[0].detections[0].results[0].hypothesis
    assert hyp.class_id == "unknown"
    assert hyp.score == pytest.approx(0.0)


def test_callback_no_faces_publishes_empty_array(node, monkeypatch):
    """Keine Gesichter -> leeres Detection2DArray wird publiziert."""
    monkeypatch.setattr(
        proc,
        "find_and_identify_faces",
        lambda image, *a, **k: ([], [], image),
    )
    node.callback(_image_msg())
    assert len(node.published_detections) == 1
    assert node.published_detections[0].detections == []


def test_callback_swallows_broken_image(node):
    """Kaputtes Image (falsche Encoding-Angabe) crasht den Node nicht."""
    broken = Image()
    broken.encoding = "not_a_real_encoding"
    broken.height = 10
    broken.width = 10
    node.callback(broken)
    assert node.published_detections == []
    assert node.published_images == []
