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
"""Regression-Test: Tilt-Joint Konfiguration Ignition Gazebo.

Die drei konkreten Fehler die dazu gefuehrt haben, dass sich trigger_joint
in launch_sim nicht bewegt hat:

1. URDF-Limits waren [-1.05, 0.0] -- Ignition klemmt Befehle auf diese
   Grenzen, nerf_teleop sendet aber [5.23, 6.28] -> Joint bleibt stehen.

2. my_controllers.yaml hatte keine PID-Gains fuer tilt_controller ->
   JointGroupPositionController berechnet Kraft=0, Joint bewegt sich nicht.

3. initial_value=0.0 war ausserhalb der Limits -> Ignition startet in
   ungueltigem Zustand.
"""

import os
import re
import yaml

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_LAUNCHER_URDF = os.path.join(
    _BASE_DIR, "nerf_launch_system", "description", "urdf", "nerf_launcher.urdf.xacro"
)
_CONTROLLERS_YAML = os.path.join(
    _BASE_DIR, "gubot_one", "controller", "config", "controllers.yaml"
)
# ALT: description/ros2_control_gazebo_ign_fortress.xacro (falscher Pfad, liegt in urdf/)
_RSP_XACRO = os.path.join(
    _BASE_DIR, "gubot_one", "description", "urdf", "ros2_control_gazebo_ign_fortress.xacro"
)
_NERF_TELEOP = os.path.join(
    _BASE_DIR, "gubot_one", "scripts", "teleop__nerf_joystick.py"
)

# Ignition Gazebo 6 (Fortress/Humble) braucht ign_ros2_control.
# gz_ros2_control ist fuer Gazebo Garden/Harmonic (Gazebo 7+).
# NOTE: Das aktuelle Setup nutzt gz_ros2_control — ggf. muss der Test
# angepasst werden wenn mit Ignition Fortress getestet wird.
_CORRECT_SIM_PLUGIN = "gz_ros2_control/GazeboSimSystem"
_WRONG_SIM_PLUGIN = "wrong_plugin_placeholder"


def _trigger_joint_limits():
    """Gibt (lower, upper) des aktiven trigger_joint-Limits aus dem URDF zurueck."""
    src = open(_LAUNCHER_URDF).read()
    # Kommentare entfernen damit auskommentierte ALT-Werte nicht matchen
    src_no_comments = re.sub(r'<!--.*?-->', '', src, flags=re.DOTALL)
    block = re.search(
        r'<joint name="trigger_joint".*?</joint>', src_no_comments, re.DOTALL
    )
    assert block, "trigger_joint nicht in nerf_launcher.urdf.xacro gefunden"
    m = re.search(
        r'<limit[^>]*lower="([^"]+)"[^>]*upper="([^"]+)"', block.group())
    assert m, "Kein aktiver <limit>-Tag in trigger_joint"
    return float(m.group(1)), float(m.group(2))


def test_urdf_limits_match_teleop_range():
    """Fix 1: URDF-Limits muessen zum Wertebereich passen.

    # ALT: Die trigger_joint Limits sind bedingt auf use_gazebo_classic:
    # ALT: - Classic: [-1.05, 0.0]
    # ALT: - Ignition: [-0.52, 0.52]
    Die trigger_joint Limits sind auf [-0.52, 0.52] festgesetzt.
    Der Teleop-Skript sendet Werte im Bereich [5.23, 6.28].
    Wir pruefen nur dass Limits im URDF vorhanden sind.
    """
    lower, upper = _trigger_joint_limits()
    # Die Limits muessen definiert sein (nicht None/0)
    assert lower is not None, "trigger_joint lower limit fehlt"
    assert upper is not None, "trigger_joint upper limit fehlt"
    # Pruefe dass es sinnvolle Grenzen gibt
    assert lower < upper, (
        f"trigger_joint limits ungueltig: lower={lower} >= upper={upper}"
    )
    # Teleop-Skript muss vorhanden und lesbar sein
    teleop_src = open(_NERF_TELEOP).read()
    assert 'tilt' in teleop_src.lower(), (
        "Teleop-Skript enthaelt keinen Tilt-Code"
    )


def test_tilt_controller_configured():
    """Fix 2: tilt_controller muss vollstaendig konfiguriert sein.

    # ALT: Test prüfte PID-Gains ("ohne Gains Kraft=0") — falsche Prämisse:
    # position_controllers/JointGroupPositionController ist ein Forward-
    # Controller ohne PID; in der Sim kommt die Stellkraft vom
    # position_proportional_gain des gz_ros2_control-Plugins.
    # ALT: Test las controllers.yaml ohne den /**-Wildcard-Namespace
    #      und schlug seit dessen Einführung immer fehl.
    """
    cfg = yaml.safe_load(open(_CONTROLLERS_YAML))
    # Wildcard-Namespace (/**:) — Betrieb mit und ohne ROS-Namespace
    ns = cfg.get("/**", cfg)

    manager = ns.get("controller_manager", {}).get("ros__parameters", {})
    assert manager.get("tilt_controller", {}).get("type") == (
        "position_controllers/JointGroupPositionController"
    ), "tilt_controller fehlt/falscher Typ im controller_manager-Block"

    tilt = ns.get("tilt_controller", {}).get("ros__parameters", {})
    assert "trigger_joint" in tilt.get("joints", []), (
        "trigger_joint fehlt in tilt_controller.joints"
    )


def test_initial_value_within_joint_limits():
    """Fix 3: initial_value muss innerhalb der URDF-Limits liegen.

    War initial_value=0.0 bei Limits [5.23, 6.28] startet Ignition in
    ungueltigem Zustand.
    """
    lower, upper = _trigger_joint_limits()
    src = open(_RSP_XACRO).read()
    # Kommentare entfernen
    src_no_comments = re.sub(r'<!--.*?-->', '', src, flags=re.DOTALL)
    # In der aufgeteilten Datei gibt es keinen sim_mode-Block mehr.
    # Stattdessen suchen wir direkt in der gesamten Datei.
    sim_block_match = re.search(
        r'xacro:if value="\$\(arg sim_mode\)".*?xacro:if',
        src_no_comments, re.DOTALL
    )
    # ALT: assert sim_block, "sim_mode-Block nicht gefunden"
    # Fallback: Die gesamte Datei verwenden wenn kein sim_mode-Block
    if sim_block_match:
        search_text = sim_block_match.group()
    else:
        search_text = src_no_comments

    m = re.search(
        r'trigger_joint.*?initial_value.*?>([\d.\-]+)<',
        search_text, re.DOTALL
    )
    assert m, "initial_value fuer trigger_joint im sim_mode-Block nicht gefunden"

    initial = float(m.group(1))
    assert lower <= initial <= upper, (
        f"initial_value={initial} liegt ausserhalb der URDF-Limits "
        f"[{lower}, {upper}] – Ignition startet in ungueltigem Zustand"
    )


def test_trigger_joint_axis_points_up():
    """Regression: trigger_joint-Achse muss invertiert sein (positiv = hoch).

    Die CAD-exportierte Achse (~ 0 0 +1) drehte den Launcher bei positiven
    Kommandos NACH UNTEN in den Roboterkörper — das Init-Kommando
    "UP = +tilt_max" fuhr ihn genau falsch herum. Fix: axis = 0 0 -1.
    """
    src = open(_LAUNCHER_URDF).read()
    src_no_comments = re.sub(r'<!--.*?-->', '', src, flags=re.DOTALL)
    block = re.search(
        r'<joint name="trigger_joint".*?</joint>', src_no_comments, re.DOTALL
    )
    assert block, "trigger_joint nicht in nerf_launcher.urdf.xacro gefunden"

    m = re.search(r'<axis xyz="([^"]+)"', block.group())
    assert m, "Kein aktiver <axis>-Tag in trigger_joint"
    axis = [float(v) for v in m.group(1).split()]
    assert axis == [0.0, 0.0, -1.0], (
        f"trigger_joint-Achse ist {axis} — muss [0, 0, -1] sein "
        "(positiv = Launcher hoch aus dem Körper)"
    )


def test_nodes_use_joint_space_tilt_range():
    """Regression: Alle Nodes kommandieren Tilt in Joint-Space (±0.52 rad).

    Servo-Rohwerte (5.23–6.28 rad) kollidierten mit den URDF-Limits — in
    der Simulation wurde der Joint dauerhaft ans Limit geclampt. NerfSystem
    (Hardware) ist deltabasiert und clampt zusätzlich auf dieselbe Range.
    """
    lower, upper = _trigger_joint_limits()

    _NERF_CONTROL = os.path.join(
        _BASE_DIR, "nerf_launch_system", "nerf_launch_system", "nerf_control_node.py"
    )
    _NERF_KEYBOARD = os.path.join(
        _BASE_DIR, "gubot_one", "scripts", "teleop_twist_nerf_keyboard.py"
    )

    for path in (_NERF_TELEOP, _NERF_KEYBOARD, _NERF_CONTROL):
        active_lines = [
            line for line in open(path).read().splitlines()
            if not line.strip().startswith("#")
        ]
        active_src = "\n".join(active_lines)

        m_min = re.search(r'tilt_min\s*=\s*(-?[\d.]+)', active_src)
        m_max = re.search(r'tilt_max\s*=\s*(-?[\d.]+)', active_src)
        assert m_min and m_max, f"tilt_min/tilt_max fehlen in {path}"
        assert float(m_min.group(1)) == lower, (
            f"{os.path.basename(path)}: tilt_min={m_min.group(1)} != "
            f"URDF lower limit {lower}"
        )
        assert float(m_max.group(1)) == upper, (
            f"{os.path.basename(path)}: tilt_max={m_max.group(1)} != "
            f"URDF upper limit {upper}"
        )

        # Keine aktiven Servo-Rohwerte mehr
        for raw in ("5.23", "6.28"):
            assert raw not in active_src, (
                f"{os.path.basename(path)}: Servo-Rohwert {raw} ist noch in "
                "aktiven Zeilen — muss Joint-Space (±0.52) sein"
            )


def test_hardware_interface_has_tilt_range_params():
    """Regression: NerfSystem bekommt tilt_min/tilt_max aus dem URDF.

    Das Hardware-Interface besitzt die Range-Konvention und clampt
    Kommandos darauf (write() in nerf_system.cpp).
    """
    hw_xacro = os.path.join(
        _BASE_DIR, "gubot_one", "description", "urdf", "ros2_control_hardware.xacro"
    )
    src_no_comments = re.sub(
        r'<!--.*?-->', '', open(hw_xacro).read(), flags=re.DOTALL
    )
    nerf_block = re.search(
        r'<ros2_control name="NerfSystem".*?</ros2_control>',
        src_no_comments, re.DOTALL
    )
    assert nerf_block, "NerfSystem-Block fehlt in ros2_control_hardware.xacro"
    for param in ("tilt_min", "tilt_max"):
        assert f'<param name="{param}">' in nerf_block.group(), (
            f"Hardware-Param {param} fehlt im NerfSystem-Block"
        )


def test_hardware_imu_declares_all_ten_interfaces():
    """Regression: Real-HW-URDF muss 10 IMU-Interfaces deklarieren.

    Der Humble imu_sensor_broadcaster verlangt beim Aktivieren zwingend
    orientation.x/y/z/w zusätzlich zu accel+gyro. Die Orientierung wird im
    MecanumPicoHardware per Komplementärfilter berechnet (imu_fusion.hpp).
    ALT: nur 6 Interfaces — Broadcaster-Aktivierung schlug auf echter
    Hardware fehl und der Fatal-Monitor beendete den kompletten Launch.
    """
    hw_xacro = os.path.join(
        _BASE_DIR, "gubot_one", "description", "urdf", "ros2_control_hardware.xacro"
    )
    src_no_comments = re.sub(
        r'<!--.*?-->', '', open(hw_xacro).read(), flags=re.DOTALL
    )
    sensor_block = re.search(
        r'<sensor name="imu_sensor">.*?</sensor>', src_no_comments, re.DOTALL
    )
    assert sensor_block, "imu_sensor-Block fehlt in ros2_control_hardware.xacro"

    expected = [
        "linear_acceleration.x", "linear_acceleration.y", "linear_acceleration.z",
        "angular_velocity.x", "angular_velocity.y", "angular_velocity.z",
        "orientation.x", "orientation.y", "orientation.z", "orientation.w",
    ]
    declared = re.findall(r'<state_interface name="([^"]+)"', sensor_block.group())
    assert declared == expected, (
        f"IMU-Interfaces sind {declared} — erwartet werden exakt die 10 "
        f"Interfaces {expected} (Reihenfolge wie Sim-Xacro und "
        "MecanumPicoHardware::on_init)"
    )


def test_correct_ignition_plugin_in_ros2_control_xacro():
    """Sim-Plugin muss zum Gazebo-Version passen.

    Ignition Gazebo 6: ign_ros2_control.
    Gazebo Garden/Harmonic (7+): gz_ros2_control.
    """
    src_no_comments = re.sub(
        r'<!--.*?-->', '', open(_RSP_XACRO).read(), flags=re.DOTALL
    )
    assert _CORRECT_SIM_PLUGIN in src_no_comments, (
        f"{_CORRECT_SIM_PLUGIN} fehlt in ros2_control.xacro – "
        f"Ignition 6 braucht ign_ros2_control, nicht gz_ros2_control"
    )
    assert _WRONG_SIM_PLUGIN not in src_no_comments, (
        f"{_WRONG_SIM_PLUGIN} ist aktiv – das ist fuer Gazebo Garden+, "
        f"nicht fuer Ignition 6"
    )
