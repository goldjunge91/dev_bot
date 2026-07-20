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
Reine Patrol-FSM-Logik (kein rclpy).

Die Quadrat-Patrouille alterniert zwischen Fahren (Bein) und einer
90-Grad-Drehung. Diese Funktionen sind der testbare Kern von
PatrolNode._on_timer.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PatrolParams:
    """Feste Parameter der Patrouille (aus den ROS-Parametern)."""

    forward_speed: float
    angular_speed: float
    leg_duration_secs: float
    num_legs: int


@dataclass(frozen=True)
class PatrolPhase:
    """Aktueller FSM-Zustand: welches Bein, und ob gerade gedreht wird."""

    leg_index: int
    turning: bool


def turn_duration_secs(angular_speed: float) -> float:
    """Dauer einer 90-Grad-Drehung bei angular_speed (rad/s)."""
    return (math.pi / 2.0) / angular_speed


def advance_phase(phase: PatrolPhase, elapsed: float, params: PatrolParams) -> tuple:
    """
    FSM-Schritt: gibt (neue Phase, phase_reset) zurueck.

    phase_reset True bedeutet: die Phasendauer ist abgelaufen, der
    Phasen-Timer muss neu gestartet werden. Uebergaenge:
    Fahren -> Drehen; Drehen -> naechstes Bein
    (leg_index = (leg_index + 1) % num_legs).
    """
    phase_duration = (
        turn_duration_secs(params.angular_speed) if phase.turning else params.leg_duration_secs
    )
    if elapsed < phase_duration:
        return phase, False
    if phase.turning:
        return (
            PatrolPhase(
                leg_index=(phase.leg_index + 1) % params.num_legs,
                turning=False,
            ),
            True,
        )
    return PatrolPhase(leg_index=phase.leg_index, turning=True), True


def command_for_phase(phase: PatrolPhase, params: PatrolParams) -> tuple:
    """Fahrkommando (linear_x, angular_z) fuer die aktuelle Phase."""
    if phase.turning:
        return 0.0, params.angular_speed
    return params.forward_speed, 0.0
