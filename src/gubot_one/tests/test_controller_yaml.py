"""
Test: my_controllers.yaml — Keine doppelten Parameter.

Prueft gemaess mecanum_drive_controller Schema (ROS2 Humble):
- Wheel-Namen: nur front_left_wheel_name (nicht _command_joint_name)
  Humble nutzt _wheel_name, _command_joint_name ist Rolling/Jazzy.
- Kinematik: wheels_radius und sum_of_... nur im kinematics:-Block, nicht flach
- YAML ist valide und ladbar

Referenz: https://control.ros.org/humble/doc/ros2_controllers/
         mecanum_drive_controller/doc/userdoc.html
"""

import os
import yaml

# Pfad relativ zu diesem Test-Skript (../config/mecanum_my_controllers.yaml)
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_CONTROLLERS_YAML = os.path.join(
    _TEST_DIR, "..", "config", "my_controllers.yaml"
)

# ROS2 Humble: Pflichtparameter ist front_left_wheel_name
# (NICHT _command_joint_name — das ist Rolling/Jazzy)
_WHEEL_NAME_KEYS = [
    "front_left_wheel_name",
    "front_right_wheel_name",
    "rear_left_wheel_name",
    "rear_right_wheel_name",
]

# Rolling/Jazzy API — auf Humble nicht unterstuetzt
_WHEEL_COMMAND_KEYS_ROLLING = [
    "front_left_wheel_command_joint_name",
    "front_right_wheel_command_joint_name",
    "rear_left_wheel_command_joint_name",
    "rear_right_wheel_command_joint_name",
]

_KINEMATICS_KEYS = [
    "wheels_radius",
    "sum_of_robot_center_projection_on_X_Y_axis",
]


def _load_mecanum_params():
    """Laedt mecanum_cont ros__parameters aus der YAML-Datei."""
    cfg = yaml.safe_load(open(_CONTROLLERS_YAML))
    return cfg.get("mecanum_cont", {}).get("ros__parameters", {})


def test_yaml_is_valid():
    """YAML muss syntaktisch korrekt und ladbar sein."""
    cfg = yaml.safe_load(open(_CONTROLLERS_YAML))
    assert isinstance(cfg, dict), "YAML root muss ein dict sein"
    assert "mecanum_cont" in cfg, "mecanum_cont fehlt in der YAML-Datei"


def test_wheel_names_present():
    """Alle vier front/rear_{left/right}_wheel_name muessen vorhanden sein.

    Dies ist laut Doku ein Pflichtparameter fuer ROS2 Humble.
    """
    params = _load_mecanum_params()
    for key in _WHEEL_NAME_KEYS:
        assert key in params, f"Pflichtparameter fehlt: {key}"
        assert params[key], f"Parameter darf nicht leer sein: {key}"


def test_no_rolling_command_joint_names():
    """Rolling/Jazzy _command_joint_name Parameter duerfen nicht vorhanden sein.

    Diese Parameter sind auf Humble nicht gueltig und fuehren zu
    uneindeutigem Verhalten.
    """
    params = _load_mecanum_params()
    for key in _WHEEL_COMMAND_KEYS_ROLLING:
        assert key not in params, (
            f"Rolling/Jazzy Parameter gefunden: '{key}' — "
            f"auf Humble heisst es '*_wheel_name'. Bitte entfernen."
        )


def test_kinematics_in_nested_block():
    """wheels_radius und sum_of_... muessen im kinematics:-Block stehen.

    Laut offiziellem Controller-Schema gehoeren sie nicht flach auf
    ros__parameters-Ebene.
    """
    params = _load_mecanum_params()
    kinematics = params.get("kinematics", {})

    assert kinematics, "kinematics:-Block fehlt in mecanum_cont"

    for key in _KINEMATICS_KEYS:
        assert key in kinematics, (
            f"Kinematik-Parameter fehlt in kinematics:-Block: {key}"
        )
        assert kinematics[key] > 0, (
            f"Kinematik-Parameter muss > 0 sein: "
            f"kinematics.{key} = {kinematics[key]}"
        )


def test_no_flat_kinematics_duplicates():
    """Kinematik-Parameter duerfen NICHT flach auf ros__parameters stehen.

    Nur im kinematics:-Block (siehe test_kinematics_in_nested_block).
    """
    params = _load_mecanum_params()
    for key in _KINEMATICS_KEYS:
        assert key not in params, (
            f"Duplikat-Parameter auf falscher Ebene: '{key}' direkt unter "
            f"ros__parameters — soll nur in kinematics:-Block stehen."
        )


def test_wheels_radius_matches_urdf():
    """wheels_radius-Wert pruefen: 0.033 m (URDF-Wert aus geometry.xacro).

    Aendert sich wenn Rad ausgetauscht wird.
    """
    params = _load_mecanum_params()
    kinematics = params.get("kinematics", {})
    radius = kinematics.get("wheels_radius", 0)
    assert abs(radius - 0.033) < 0.001, (
        f"wheels_radius={radius} stimmt nicht mit URDF-Wert 0.033 ueberein"
    )
