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
rclpy-Integrationstests fuer FireAtFace.

Echter Graph: FireAtFace-Node + Mock-/nerf/fire-Trigger-Server.
Deterministisch: listener_callback wird direkt aufgerufen, der
Cooldown ueber last_fire_time manipuliert (kein sleep).
"""

import time

import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from std_srvs.srv import Trigger
from vision_msgs.msg import (
    BoundingBox2D,
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)

from face_tracker.fire_at_face import FireAtFace


@pytest.fixture(scope="module")
def rclpy_ctx():
    """ROS-Kontext einmal pro Modul."""
    rclpy.init()
    yield
    rclpy.shutdown()


def make_msg(class_id="alice", cx=0.5, cy=0.5, size=0.3):
    """Baut ein echtes Detection2DArray mit einer Detection."""
    det = Detection2D()
    bbox = BoundingBox2D()
    bbox.center.position.x = float(cx)
    bbox.center.position.y = float(cy)
    bbox.size_x = float(size)
    bbox.size_y = float(size)
    det.bbox = bbox
    hyp = ObjectHypothesisWithPose()
    hyp.hypothesis.class_id = class_id
    det.results.append(hyp)
    msg = Detection2DArray()
    msg.detections.append(det)
    return msg


class FireRig:
    """Testaufbau: FireAtFace + Mock-Feuer-Server + Executor."""

    def __init__(self):
        self.node = FireAtFace()
        self.server = rclpy.create_node("mock_nerf")
        self.fire_calls = []
        self.server.create_service(Trigger, "/nerf/fire", self._on_fire)
        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.node)
        self.executor.add_node(self.server)
        # Cooldown initial abgelaufen (Node startet mit last_fire_time=0.0,
        # explizit rueckdatieren macht die Absicht sichtbar).
        self.node.last_fire_time = time.time() - 1000.0

    def _on_fire(self, request, response):
        self.fire_calls.append(request)
        response.success = True
        response.message = "pew"
        return response

    def spin_until(self, predicate, timeout=3.0):
        """Spinnt bis predicate() wahr ist oder timeout ablaeuft."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.executor.spin_once(timeout_sec=0.05)
            if predicate():
                return True
        return predicate()

    def settle(self, duration=0.3):
        """Spinnt eine feste Zeit, um Nicht-Ereignisse zu verifizieren."""
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            self.executor.spin_once(timeout_sec=0.05)

    def shutdown(self):
        self.executor.remove_node(self.node)
        self.executor.remove_node(self.server)
        self.node.destroy_node()
        self.server.destroy_node()


@pytest.fixture
def rig(rclpy_ctx):
    """Frischer Aufbau pro Test; wartet auf Service-Discovery."""
    r = FireRig()
    assert r.spin_until(lambda: r.node.fire_client.service_is_ready(), timeout=5.0)
    yield r
    r.shutdown()


def test_fires_once_when_locked(rig):
    """Zentriert + gross genug -> genau ein Service-Call."""
    rig.node.listener_callback(make_msg())
    assert rig.spin_until(lambda: len(rig.fire_calls) == 1)
    # Direkt danach blockt der frisch gesetzte Cooldown.
    rig.node.listener_callback(make_msg())
    rig.settle()
    assert len(rig.fire_calls) == 1


def test_cooldown_blocks_fire(rig):
    """Laufender Cooldown -> kein Service-Call."""
    rig.node.last_fire_time = time.time()
    rig.node.listener_callback(make_msg())
    rig.settle()
    assert rig.fire_calls == []


def test_fires_again_after_cooldown(rig):
    """Abgelaufener Cooldown -> naechster Schuss."""
    rig.node.listener_callback(make_msg())
    assert rig.spin_until(lambda: len(rig.fire_calls) == 1)
    rig.node.last_fire_time = time.time() - rig.node.cooldown_secs - 1.0
    rig.node.listener_callback(make_msg())
    assert rig.spin_until(lambda: len(rig.fire_calls) == 2)


def test_off_center_does_not_fire(rig):
    """Ziel ausserhalb der X-Toleranz -> kein Schuss."""
    rig.node.listener_callback(make_msg(cx=0.8))
    rig.settle()
    assert rig.fire_calls == []


def test_too_small_does_not_fire(rig):
    """Ziel zu klein (zu weit weg) -> kein Schuss."""
    rig.node.listener_callback(make_msg(size=0.05))
    rig.settle()
    assert rig.fire_calls == []


def test_target_person_is_respected(rig):
    """Mit target_person feuert der Node nur auf diese Person."""
    rig.node.target_person = "alice"
    rig.node.listener_callback(make_msg(class_id="bob"))
    rig.settle()
    assert rig.fire_calls == []
    rig.node.listener_callback(make_msg(class_id="alice"))
    assert rig.spin_until(lambda: len(rig.fire_calls) == 1)
