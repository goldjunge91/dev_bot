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
"""Unit-Tests fuer die reine Patrol-FSM (patrol_logic, kein rclpy)."""

import math

import pytest

from gubot_patrol.patrol_logic import (
    PatrolParams,
    PatrolPhase,
    advance_phase,
    command_for_phase,
    turn_duration_secs,
)

PARAMS = PatrolParams(
    forward_speed=0.15,
    angular_speed=0.6,
    leg_duration_secs=4.0,
    num_legs=4,
)


def test_turn_duration_is_quarter_turn():
    """90-Grad-Drehung: (pi/2) / angular_speed."""
    assert turn_duration_secs(0.6) == pytest.approx(math.pi / 2.0 / 0.6)


def test_leg_phase_holds_before_expiry():
    """Vor Ablauf der Bein-Dauer bleibt die Phase unveraendert."""
    phase = PatrolPhase(leg_index=1, turning=False)
    new_phase, reset = advance_phase(phase, 3.9, PARAMS)
    assert new_phase == phase
    assert reset is False


def test_leg_expiry_starts_turn():
    """Nach Ablauf des Beins beginnt die Drehung (gleiches Bein)."""
    phase = PatrolPhase(leg_index=2, turning=False)
    new_phase, reset = advance_phase(phase, 4.0, PARAMS)
    assert new_phase == PatrolPhase(leg_index=2, turning=True)
    assert reset is True


def test_turn_expiry_advances_leg():
    """Nach Ablauf der Drehung: naechstes Bein, Drehen beendet."""
    phase = PatrolPhase(leg_index=0, turning=True)
    turn_time = turn_duration_secs(PARAMS.angular_speed)
    new_phase, reset = advance_phase(phase, turn_time + 0.01, PARAMS)
    assert new_phase == PatrolPhase(leg_index=1, turning=False)
    assert reset is True


def test_turn_phase_holds_before_expiry():
    """Vor Ablauf der Drehdauer wird weitergedreht."""
    phase = PatrolPhase(leg_index=0, turning=True)
    turn_time = turn_duration_secs(PARAMS.angular_speed)
    new_phase, reset = advance_phase(phase, turn_time * 0.5, PARAMS)
    assert new_phase == phase
    assert reset is False


def test_leg_index_wraps_modulo_num_legs():
    """Letztes Bein + Drehung -> zurueck zu Bein 0."""
    phase = PatrolPhase(leg_index=PARAMS.num_legs - 1, turning=True)
    new_phase, _ = advance_phase(phase, 100.0, PARAMS)
    assert new_phase.leg_index == 0
    assert new_phase.turning is False


def test_command_forward_during_leg():
    """Bein-Phase faehrt vorwaerts, keine Drehung."""
    cmd = command_for_phase(PatrolPhase(leg_index=0, turning=False), PARAMS)
    assert cmd == (PARAMS.forward_speed, 0.0)


def test_command_rotation_during_turn():
    """Dreh-Phase dreht auf der Stelle."""
    cmd = command_for_phase(PatrolPhase(leg_index=0, turning=True), PARAMS)
    assert cmd == (0.0, PARAMS.angular_speed)


def test_full_square_cycle_returns_to_start():
    """8 Phasenablaeufe (4 Beine + 4 Drehungen) = ein voller Zyklus."""
    phase = PatrolPhase(leg_index=0, turning=False)
    for _ in range(8):
        phase, reset = advance_phase(phase, 1e9, PARAMS)
        assert reset is True
    assert phase == PatrolPhase(leg_index=0, turning=False)
