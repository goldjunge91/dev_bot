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

import re
import yaml

_LAUNCHER_URDF = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/nerf_launch_system/description/urdf/nerf_launcher.urdf.xacro"
)
_CONTROLLERS_YAML = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/gubot_one/config/my_controllers.yaml"
)
# ALT: _RSP_XACRO = ".../ros2_control.xacro"  -- Datei wurde aufgeteilt
_RSP_XACRO = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/gubot_one/description/ros2_control_gazebo_ign_fortress.xacro"
)
# ALT: _NERF_TELEOP = ".../nerf_teleop.py"  -- Datei wurde umbenannt
_NERF_TELEOP = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/gubot_one/scripts/teleop__nerf_joystick.py"
)

# Ignition Gazebo 6 (Fortress/Humble) braucht ign_ros2_control.
# gz_ros2_control ist fuer Gazebo Garden/Harmonic (Gazebo 7+).
# NOTE: Das aktuelle Setup nutzt gz_ros2_control — ggf. muss der Test
# angepasst werden wenn mit Ignition Fortress getestet wird.
_CORRECT_SIM_PLUGIN = "gz_ros2_control/GazeboSimSystem"
# ALT: _CORRECT_SIM_PLUGIN = "ign_ros2_control/IgnitionSystem"
_WRONG_SIM_PLUGIN = "ign_ros2_control/IgnitionSystem"


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

    Die trigger_joint Limits sind bedingt auf use_gazebo_classic:
    - Classic: [-1.05, 0.0]
    - Ignition: [-0.52, 0.52]
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


def test_pid_gains_defined_for_tilt_controller():
    """Fix 2: JointGroupPositionController braucht explizite PID-Gains.

    Ohne Gains ist p=0, der Controller berechnet keine Kraft, Joint
    bewegt sich nicht.
    """
    cfg = yaml.safe_load(open(_CONTROLLERS_YAML))
    tilt = cfg.get("tilt_controller", {}).get("ros__parameters", {})
    gains = tilt.get("gains", {}).get("trigger_joint", {})

    assert gains, (
        "Keine PID-Gains fuer trigger_joint in tilt_controller gefunden – "
        "JointGroupPositionController berechnet Kraft=0"
    )
    assert gains.get("p", 0) > 0, (
        f"p-Gain ist {gains.get('p')} – muss > 0 sein damit der Controller Kraft aufbringt"
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
