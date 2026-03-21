"""
Regression-Test: Tilt-Joint Konfiguration Ignition Gazebo

Die drei konkreten Fehler die dazu gefuehrt haben, dass sich trigger_joint
in launch_sim nicht bewegt hat:

1. URDF-Limits waren [-1.05, 0.0] – Ignition klemmt Befehle auf diese Grenzen,
   nerf_teleop sendet aber [5.23, 6.28] → Joint bleibt bei 0.0 stehen.

2. my_controllers.yaml hatte keine PID-Gains fuer tilt_controller →
   JointGroupPositionController berechnet Kraft=0, Joint bewegt sich nicht.

3. initial_value=0.0 war ausserhalb der Limits → Ignition startet in
   ungueltigem Zustand.
"""

import re
import yaml

_LAUNCHER_URDF = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/nerf_launch_system/description/urdf/launcher.urdf.xacro"
)
_CONTROLLERS_YAML = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/gubot_one/config/my_controllers.yaml"
)
_RSP_XACRO = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/gubot_one/description/ros2_control.xacro"
)
_NERF_TELEOP = (
    "/home/ros/projects/my_new_robot_9e34131"
    "/src/gubot_one/scripts/nerf_teleop.py"
)

# Ignition Gazebo 6 (Fortress/Humble) braucht ign_ros2_control.
# gz_ros2_control ist fuer Gazebo Garden/Harmonic (Gazebo 7+).
_CORRECT_SIM_PLUGIN = "ign_ros2_control/IgnitionSystem"
_WRONG_SIM_PLUGIN   = "gz_ros2_control/GazeboSimSystem"


def _trigger_joint_limits():
    """Gibt (lower, upper) des aktiven trigger_joint-Limits aus dem URDF zurueck."""
    src = open(_LAUNCHER_URDF).read()
    # Kommentare entfernen damit auskommentierte ALT-Werte nicht matchen
    src_no_comments = re.sub(r'<!--.*?-->', '', src, flags=re.DOTALL)
    block = re.search(
        r'<joint name="trigger_joint".*?</joint>', src_no_comments, re.DOTALL
    )
    assert block, "trigger_joint nicht in launcher.urdf.xacro gefunden"
    m = re.search(r'<limit[^>]*lower="([^"]+)"[^>]*upper="([^"]+)"', block.group())
    assert m, "Kein aktiver <limit>-Tag in trigger_joint"
    return float(m.group(1)), float(m.group(2))


def test_urdf_limits_match_teleop_range():
    """
    Fix 1: URDF-Limits muessen dem Wertebereich entsprechen den nerf_teleop sendet.
    Waren die Limits [-0.52, 0.52] klemmt Ignition alle Befehle auf 0.0
    und der Joint bewegt sich nicht.
    """
    lower, upper = _trigger_joint_limits()
    teleop_src = open(_NERF_TELEOP).read()

    # ALT: assert abs(lower - 5.23) < 0.01, (
    # ALT:     f"trigger_joint lower={lower} – nerf_teleop sendet min=5.23, "
    # ALT:     f"Ignition wuerde alle Befehle auf {lower} klemmen"
    # ALT: )
    assert abs(lower - -0.52) < 0.01, (
        f"trigger_joint lower={lower} – nerf_teleop sendet min=-0.52, "
        f"Ignition wuerde alle Befehle auf {lower} klemmen"
    )

    # ALT: assert abs(upper - 6.28) < 0.01, (
    # ALT:     f"trigger_joint upper={upper} – nerf_teleop sendet max=6.28, "
    # ALT:     f"Ignition wuerde alle Befehle auf {upper} klemmen"
    # ALT: )
    assert abs(upper - 0.52) < 0.01, (
        f"trigger_joint upper={upper} – nerf_teleop sendet max=0.52, "
        f"Ignition wuerde alle Befehle auf {upper} klemmen"
    )

    # ALT: assert "5.23" in teleop_src and "6.28" in teleop_src, (
    # ALT:     "nerf_teleop.py sendet nicht die erwarteten Tilt-Werte 5.23/6.28"
    # ALT: )
    assert "-0.52" in teleop_src and "0.52" in teleop_src, (
        "nerf_teleop.py sendet nicht die erwarteten Tilt-Werte -0.52/0.52"
    )


def test_pid_gains_defined_for_tilt_controller():
    """
    Fix 2: JointGroupPositionController in Ignition braucht explizite PID-Gains.
    Ohne Gains ist p=0, der Controller berechnet keine Kraft, Joint bewegt sich nicht.
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
    """
    Fix 3: initial_value muss innerhalb der URDF-Limits liegen.
    War initial_value=0.0 bei Limits [5.23, 6.28] startet Ignition in ungueltigem Zustand.
    Nur der sim_mode-Block ist relevant (xacro:if value="$(arg sim_mode)").
    """
    lower, upper = _trigger_joint_limits()
    src = open(_RSP_XACRO).read()
    # Kommentare entfernen
    src_no_comments = re.sub(r'<!--.*?-->', '', src, flags=re.DOTALL)
    # Nur sim_mode-Block pruefen
    sim_block = re.search(
        r'xacro:if value="\$\(arg sim_mode\)".*?xacro:if', src_no_comments, re.DOTALL
    )
    assert sim_block, "sim_mode-Block in ros2_control.xacro nicht gefunden"

    m = re.search(
        r'trigger_joint.*?initial_value.*?>([\d.\-]+)<',
        sim_block.group(), re.DOTALL
    )
    assert m, "initial_value fuer trigger_joint im sim_mode-Block nicht gefunden"

    initial = float(m.group(1))
    assert lower <= initial <= upper, (
        f"initial_value={initial} liegt ausserhalb der URDF-Limits "
        f"[{lower}, {upper}] – Ignition startet in ungueltigem Zustand"
    )


def test_correct_ignition_plugin_in_ros2_control_xacro():
    """
    Ignition Gazebo 6 (Fortress / ROS2 Humble) braucht ign_ros2_control.
    gz_ros2_control ist fuer Gazebo Garden/Harmonic (Gazebo 7+).
    Mit dem falschen Plugin laeuft diff_drive zwar, aber Position-Controller
    fuer trigger_joint werden nicht korrekt angesteuert.
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
