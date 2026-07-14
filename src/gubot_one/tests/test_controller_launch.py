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
"""Test: controller.launch.py — Mecanum Konfiguration.

# ALT: Datei hieß test_launch_robot.py und prüfte bringup/launch/launch_robot.launch.py.
#      launch_robot.launch.py wurde durch die modulare Kette
#      controller/launch/controller.launch.py ersetzt.

- Der Spawner muss 'mecanum_drive_controller' starten.
- Das twist_mux Remapping muss auf '/mecanum_drive_controller/cmd_vel_unstamped' zeigen.
- Der controller_manager (ros2_control_node) muss für echte Hardware gestartet werden.

Ansatz: Kombination aus Textanalyse (zuverlaessig) und LaunchDescription
Introspection.
"""

import os
import importlib.util

from launch import LaunchDescription  # noqa: F401
from launch.actions import DeclareLaunchArgument

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# ALT: bringup/launch/launch_robot.launch.py — Datei geloescht
_LAUNCH_FILE = os.path.join(
    _TEST_DIR, "..", "controller", "launch", "controller.launch.py"
)


def _load_launch_source():
    """Laedt den Quelltext der Launch-Datei."""
    with open(_LAUNCH_FILE) as f:
        return f.read()


def _load_launch_description():
    """Laedt die LaunchDescription aus controller.launch.py."""
    spec = importlib.util.spec_from_file_location(
        "controller_launch", _LAUNCH_FILE
    )
    launch_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launch_mod)
    return launch_mod.generate_launch_description()


def _active_source():
    """Quelltext ohne Kommentarzeilen."""
    source = _load_launch_source()
    active_lines = [
        line.strip() for line in source.splitlines()
        if not line.strip().startswith("#")
    ]
    return "\n".join(active_lines)


def test_launch_arguments():
    """Prueft ob Launch-Argumente vorhanden sind."""
    ld = _load_launch_description()

    found = {"use_nerf_hardware": False, "auto_arm": False}
    for action in ld.entities:
        if isinstance(action, DeclareLaunchArgument) and action.name in found:
            found[action.name] = True
    for name, present in found.items():
        assert present, f"Launch-Argument '{name}' fehlt"


def test_controller_configuration():
    """Prueft ob mecanum_drive_controller Spawner konfiguriert ist."""
    active_source = _active_source()

    assert "mecanum_drive_controller" in active_source, (
        "Spawner fuer mecanum_drive_controller fehlt in aktiven Zeilen"
    )

    # diff_cont darf nicht in aktiven argument-Zeilen vorkommen
    diff_cont_active = any(
        "diff_cont" in line and "arguments" in line
        for line in active_source.splitlines()
    )
    assert not diff_cont_active, (
        "Spawner fuer diff_cont ist noch in aktiver Konfiguration"
    )


def test_controller_manager_node():
    """Prueft ob der controller_manager (ros2_control_node) gestartet wird.

    Ohne ihn laufen die Spawner auf echter Hardware ins Leere — in der
    Simulation uebernimmt das gz_ros2_control-Plugin.
    """
    active_source = _active_source()

    assert "ros2_control_node" in active_source, (
        "controller_manager (ros2_control_node) fehlt in aktiven Zeilen"
    )
    assert "UnlessCondition(use_sim_time)" in active_source, (
        "ros2_control_node muss auf echte Hardware beschraenkt sein "
        "(UnlessCondition(use_sim_time))"
    )


def test_nerf_chain():
    """Prueft ob die Nerf-Controller-Kette konfiguriert ist."""
    active_source = _active_source()

    for controller in ("tilt_controller", "shooter_controller", "arming_controller"):
        assert f'"{controller}"' in active_source, (
            f"Spawner fuer {controller} fehlt in aktiven Zeilen"
        )
    assert "nerf_control_node" in active_source, (
        "nerf_control_node fehlt in aktiven Zeilen"
    )


def test_twist_mux_remap():
    """Prueft das Remapping von twist_mux auf den gemeinsamen /cmd_vel Vertrag."""
    active_source = _active_source()

    assert '("/cmd_vel_out", "/cmd_vel")' in active_source, (
        "twist_mux remap auf /cmd_vel fehlt in aktiven Zeilen"
    )

    # ALT diff_cont remap darf nicht aktiv sein
    assert "/diff_cont/cmd_vel_unstamped" not in active_source, (
        "Altes diff_cont remap ist noch aktiv — muss auskommentiert sein"
    )


def test_controller_manager_remappings():
    """Prueft die Sim/Real-Topic-Paritaet am ros2_control_node.

    Die Remappings muessen die <ros>-Remappings des gz-Plugins spiegeln,
    sonst bekommt die EKF (odometry/wheels, imu/data) auf echter Hardware
    keine Inputs.
    """
    active_source = _active_source()

    expected = [
        '("mecanum_drive_controller/cmd_vel_unstamped", "cmd_vel")',
        '("mecanum_drive_controller/odom", "odometry/wheels")',
        '("imu_broadcaster/imu", "imu/data")',
        '("~/robot_description", "robot_description")',
    ]
    for remap in expected:
        assert remap in active_source, (
            f"ros2_control_node Remapping {remap} fehlt in aktiven Zeilen"
        )
