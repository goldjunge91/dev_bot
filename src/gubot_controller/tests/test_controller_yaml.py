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
"""Test: controllers.yaml — Keine doppelten Parameter.

Prueft gemaess mecanum_drive_controller Schema (ROS2 Humble):
- Wheel-Namen: nur front_left_wheel_name (nicht _command_joint_name)
  Humble nutzt _wheel_name, _command_joint_name ist Rolling/Jazzy.
- Kinematik: wheel_separation_x/y und wheel_radius direkt unter ros__parameters
- YAML ist valide und ladbar

Referenz: https://control.ros.org/humble/doc/ros2_controllers/
         mecanum_drive_controller/doc/userdoc.html
"""

import os
import yaml

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# config/ liegt im selben Paket (gubot_controller)
# NEU: Referenz-Struktur, YAML liegt unter controller/config/controllers.yaml
_CONTROLLERS_YAML = os.path.join(
    _TEST_DIR, "..", "config", "controllers.yaml"
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

# mecanum_drive_controller — Referenz-Schema
_CONTROLLER_KEY = "mecanum_drive_controller"


def _load_mecanum_params():
    """Laedt mecanum_drive_controller ros__parameters aus der YAML-Datei."""
    cfg = yaml.safe_load(open(_CONTROLLERS_YAML))
    # Suche unter /**/ros__parameters (Wildcard-Namespace-Schema)
    for key, val in cfg.items():
        if isinstance(val, dict) and _CONTROLLER_KEY in val:
            return val[_CONTROLLER_KEY].get("ros__parameters", {})
    # Fallback: direkt auf oberster Ebene
    return cfg.get(_CONTROLLER_KEY, {}).get("ros__parameters", {})


def test_yaml_is_valid():
    """YAML muss syntaktisch korrekt und ladbar sein."""
    cfg = yaml.safe_load(open(_CONTROLLERS_YAML))
    assert isinstance(cfg, dict), "YAML root muss ein dict sein"
    # Pruefe ob mecanum_drive_controller irgendwo in der verschachtelten Struktur vorkommt
    yaml_str = open(_CONTROLLERS_YAML).read()
    assert _CONTROLLER_KEY in yaml_str, (
        f"{_CONTROLLER_KEY} fehlt in der YAML-Datei"
    )


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
    """wheel_separation_x/y und wheel_radius muessen in ros__parameters stehen.

    Im Humble-Schema (nicht Rolling) stehen diese direkt unter ros__parameters,
    nicht in einem separaten kinematics-Block.
    """
    params = _load_mecanum_params()
    # Direkte Parameter auf ros__parameters-Ebene
    assert "wheel_separation_x" in params, (
        "wheel_separation_x fehlt in mecanum_drive_controller.ros__parameters"
    )
    assert "wheel_separation_y" in params, (
        "wheel_separation_y fehlt in mecanum_drive_controller.ros__parameters"
    )
    assert "wheel_radius" in params, (
        "wheel_radius fehlt in mecanum_drive_controller.ros__parameters"
    )
    assert params["wheel_radius"] > 0, (
        f"wheel_radius muss > 0 sein, ist: {params['wheel_radius']}"
    )


def test_no_flat_kinematics_duplicates():
    """sum_of_robot_center_projection Schluessel darf nicht vorhanden sein.

    Dieser Schluessel gehoert zum Rolling/Jazzy kinematics-Block-Schema,
    nicht zu Humble.
    """
    params = _load_mecanum_params()
    assert "sum_of_robot_center_projection_on_X_Y_axis" not in params, (
        "Rolling/Jazzy kinematics-Parameter 'sum_of_robot_center_projection_on_X_Y_axis' "
        "gefunden — nicht gueltig auf Humble."
    )


def test_wheels_radius_matches_urdf():
    """wheels_radius-Wert pruefen: 0.05 m (URDF-Wert aus geometry.xacro,
    100mm Aluminum-Mecanum-Rad).

    Aendert sich wenn Rad ausgetauscht wird.
    """
    params = _load_mecanum_params()
    radius = params.get("wheel_radius", 0)
    assert abs(radius - 0.05) < 0.001, (
        f"wheel_radius={radius} stimmt nicht mit URDF-Wert 0.05 ueberein"
    )
