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
rclpy-Integrationstests fuer PatrolNode.

Deterministisch: der Node-Timer wird gecancelt, _on_timer/_on_set_enabled
werden direkt aufgerufen; Phasenwechsel via rueckdatiertem _phase_start.
"""

import math
import time

import pytest
import rclpy
from geometry_msgs.msg import Twist
from rclpy.duration import Duration
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import Bool
from std_srvs.srv import SetBool

from gubot_patrol.patrol_node import PatrolNode


@pytest.fixture(scope="module")
def rclpy_ctx():
    """ROS-Kontext einmal pro Modul."""
    rclpy.init()
    yield
    rclpy.shutdown()


class PatrolRig:
    """Testaufbau: PatrolNode + Probe-Node + Executor."""

    def __init__(self):
        self.node = PatrolNode()
        self.node.timer.cancel()
        self.probe = rclpy.create_node("patrol_probe")
        self.twists = []
        self.actives = []
        self.probe.create_subscription(Twist, "cmd_vel_nav", self.twists.append, 10)
        self.probe.create_subscription(Bool, "/patrol_node/active", self.actives.append, 10)
        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.node)
        self.executor.add_node(self.probe)

    def spin_until(self, predicate, timeout=2.0):
        """Spinnt bis predicate() wahr ist oder timeout (Wanduhr) ablaeuft."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.executor.spin_once(timeout_sec=0.05)
            if predicate():
                return True
        return predicate()

    def backdate_phase(self, seconds):
        """Setzt den Phasenstart in die Vergangenheit."""
        self.node._phase_start = self.node.get_clock().now() - Duration(seconds=seconds)

    def shutdown(self):
        self.executor.remove_node(self.node)
        self.executor.remove_node(self.probe)
        self.node.destroy_node()
        self.probe.destroy_node()


@pytest.fixture
def rig(rclpy_ctx):
    """Frischer Aufbau pro Test."""
    r = PatrolRig()
    # Discovery zwischen Node und Probe abwarten
    r.spin_until(lambda: r.probe.count_publishers("cmd_vel_nav") > 0, timeout=5.0)
    yield r
    r.shutdown()


def test_default_parameters_applied(rig):
    """Defaults entsprechen patrol_params.yaml."""
    assert rig.node.forward_speed == pytest.approx(0.15)
    assert rig.node.angular_speed == pytest.approx(0.6)
    assert rig.node.num_legs == 4
    assert rig.node.enabled is True
    assert rig.node.turn_duration_secs == pytest.approx(math.pi / 2.0 / 0.6)


def test_timer_publishes_forward_and_active_when_enabled(rig):
    """Ein Timer-Tick in der Bein-Phase: Vorwaerts-Twist + active=True."""
    rig.node._on_timer()
    assert rig.spin_until(lambda: rig.twists and rig.actives)
    assert rig.twists[-1].linear.x == pytest.approx(0.15)
    assert rig.twists[-1].angular.z == pytest.approx(0.0)
    assert rig.actives[-1].data is True


def test_backdated_phase_start_triggers_turn(rig):
    """Abgelaufenes Bein (> 4 s) -> Drehphase mit angular_speed."""
    rig.backdate_phase(5.0)
    rig.node._on_timer()
    assert rig.node._turning is True
    assert rig.spin_until(lambda: rig.twists)
    assert rig.twists[-1].angular.z == pytest.approx(0.6)
    assert rig.twists[-1].linear.x == pytest.approx(0.0)


def test_turn_completion_advances_leg(rig):
    """Abgelaufene Drehung -> naechstes Bein, wieder Vorwaertsfahrt."""
    rig.node._turning = True
    rig.backdate_phase(rig.node.turn_duration_secs + 0.1)
    rig.node._on_timer()
    assert rig.node._turning is False
    assert rig.node._leg_index == 1


def test_set_enabled_false_publishes_stop_and_gates_timer(rig):
    """Deaktivieren: Stop-Twist, danach keine Fahrkommandos mehr."""
    response = rig.node._on_set_enabled(SetBool.Request(data=False), SetBool.Response())
    assert response.success is True
    assert response.message == "patrol disabled"
    assert rig.spin_until(lambda: rig.twists)
    stop = rig.twists[-1]
    assert stop.linear.x == pytest.approx(0.0)
    assert stop.angular.z == pytest.approx(0.0)

    rig.twists.clear()
    rig.node._on_timer()
    assert rig.spin_until(lambda: rig.actives)
    assert rig.actives[-1].data is False
    assert rig.twists == []


def test_set_enabled_true_reenables(rig):
    """Re-Enable: Timer publiziert wieder Fahrkommandos."""
    rig.node._on_set_enabled(SetBool.Request(data=False), SetBool.Response())
    rig.node._on_set_enabled(SetBool.Request(data=True), SetBool.Response())
    rig.node._on_timer()
    # Der Stop-Twist des Disable kann noch in Zustellung sein — explizit
    # auf das Vorwaerts-Kommando warten.
    assert rig.spin_until(lambda: any(t.linear.x > 0.0 for t in rig.twists))
