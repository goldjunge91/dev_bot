# Copyright 2024 gubot_one contributors
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
"""Test: launch_robot.launch.py — Mecanum Konfiguration.

# ALT: - Der Spawner muss 'mecanum_cont' starten.
# ALT: - Das twist_mux Remapping muss auf '/mecanum_cont/cmd_vel_unstamped' zeigen.
- Der Spawner muss 'mecanum_drive_controller' starten.
- Das twist_mux Remapping muss auf '/mecanum_drive_controller/cmd_vel_unstamped' zeigen.

Ansatz: Kombination aus Textanalyse (zuverlaessig) und LaunchDescription
Introspection.
"""

import os
import importlib.util

from launch import LaunchDescription  # noqa: F401
from launch.actions import DeclareLaunchArgument

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# ALT: tests/../launch/launch_robot.launch.py — falscher Pfad (Datei liegt in bringup/launch)
# NEU: bringup/launch/launch_robot.launch.py
_LAUNCH_FILE = os.path.join(
    _TEST_DIR, "..", "bringup", "launch", "launch_robot.launch.py"
)


def _load_launch_source():
    """Laedt den Quelltext der Launch-Datei."""
    with open(_LAUNCH_FILE) as f:
        return f.read()


def _load_launch_description():
    """Laedt die LaunchDescription aus launch_robot.launch.py."""
    spec = importlib.util.spec_from_file_location("launch_robot", _LAUNCH_FILE)
    launch_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launch_mod)
    return launch_mod.generate_launch_description()


def test_launch_arguments():
    """Prueft ob Launch-Argumente vorhanden sind."""
    ld = _load_launch_description()

    found_nerf = False
    for action in ld.entities:
        if (isinstance(action, DeclareLaunchArgument)
                and action.name == "use_nerf_hardware"):
            found_nerf = True
            break
    assert found_nerf, "Launch-Argument 'use_nerf_hardware' fehlt"


def test_controller_configuration():
    # ALT: """Prueft ob mecanum_cont Spawner konfiguriert ist."""
    # ALT: assert "mecanum_cont" in active_source, (
    # ALT:     "Spawner fuer mecanum_cont fehlt in aktiven Zeilen"
    # ALT: )
    """Prueft ob mecanum_drive_controller Spawner konfiguriert ist."""
    source = _load_launch_source()

    # mecanum_drive_controller Spawner muss vorhanden sein (nicht auskommentiert)
    active_lines = [
        line.strip() for line in source.splitlines()
        if not line.strip().startswith("#")
    ]
    active_source = "\n".join(active_lines)

    assert "mecanum_drive_controller" in active_source, (
        "Spawner fuer mecanum_drive_controller fehlt in aktiven Zeilen"
    )

    # diff_cont darf nicht in aktiven argument-Zeilen vorkommen
    diff_cont_active = any(
        "diff_cont" in line and "arguments" in line
        for line in active_lines
    )
    assert not diff_cont_active, (
        "Spawner fuer diff_cont ist noch in aktiver Konfiguration"
    )


def test_twist_mux_remap():
    # ALT: """Prueft das Remapping von twist_mux auf mecanum_cont."""
    # ALT: assert "/mecanum_cont/cmd_vel_unstamped" in active_source, (
    # ALT:     "twist_mux remap auf /mecanum_cont/cmd_vel_unstamped fehlt "
    # ALT:     "in aktiven Zeilen"
    # ALT: )
    """Prueft das Remapping von twist_mux auf mecanum_drive_controller."""
    source = _load_launch_source()

    active_lines = [
        line.strip() for line in source.splitlines()
        if not line.strip().startswith("#")
    ]
    active_source = "\n".join(active_lines)

    assert "/mecanum_drive_controller/cmd_vel_unstamped" in active_source, (
        "twist_mux remap auf /mecanum_drive_controller/cmd_vel_unstamped fehlt "
        "in aktiven Zeilen"
    )

    # ALT diff_cont remap darf nicht aktiv sein
    assert "/diff_cont/cmd_vel_unstamped" not in active_source, (
        "Altes diff_cont remap ist noch aktiv — muss auskommentiert sein"
    )
