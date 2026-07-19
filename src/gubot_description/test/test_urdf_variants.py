# Copyright 2026 gubot_one contributors
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
Test: Alle URDF-Varianten rendern und strukturell korrekt.

Prueft die xacro-Varianten-Matrix (sim/hw x nerf x depth_camera), die
stabilen Link-/Joint-Namen, die ros2_control-Bloecke, das Mecanum-
Reibungsmodell (fdir1) und die Konsistenz der Rad-Geometrie zwischen
config/robot_dimensions.yaml und gubot_controller/config/controllers.yaml.
"""

import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import pytest
import yaml

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PKG_DIR = os.path.join(_TEST_DIR, "..")
_SRC_DIR = os.path.join(_PKG_DIR, "..")
XACRO_PATH = os.path.join(_PKG_DIR, "urdf", "gubot_one_main.urdf.xacro")
DIMENSIONS_YAML = os.path.join(_PKG_DIR, "config", "robot_dimensions.yaml")
CONTROLLERS_YAML = os.path.join(
    _SRC_DIR, "gubot_controller", "config", "controllers.yaml"
)

BASE_JOINTS = {
    "base_to_body_joint", "imu_joint", "laser_joint",
    "camera_joint", "camera_optical_joint", "face_joint",
    "fl_wheel_joint", "fr_wheel_joint", "rl_wheel_joint", "rr_wheel_joint",
}
BASE_LINKS = {
    "base_link", "body_link", "imu_link", "laser_frame",
    "camera_link", "camera_link_optical", "face_link",
    "fl_wheel_link", "fr_wheel_link", "rl_wheel_link", "rr_wheel_link",
}
IMU_INTERFACES = [
    "linear_acceleration.x", "linear_acceleration.y", "linear_acceleration.z",
    "angular_velocity.x", "angular_velocity.y", "angular_velocity.z",
    "orientation.x", "orientation.y", "orientation.z", "orientation.w",
]


def render(*extra_args):
    """Rendert das Haupt-XACRO mit den gegebenen Argumenten."""
    result = subprocess.run(
        ["xacro", XACRO_PATH, *extra_args],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"XACRO rendering failed ({extra_args}): {result.stderr}")
    return result.stdout


VARIANTS = [
    ("sim_mode:=true", "use_nerf_hardware:=false"),
    ("sim_mode:=true", "use_nerf_hardware:=true"),
    ("sim_mode:=false", "use_nerf_hardware:=false"),
    ("sim_mode:=false", "use_nerf_hardware:=true"),
    ("sim_mode:=true", "use_nerf_hardware:=false", "use_depth_camera:=true"),
    ("sim_mode:=false", "use_nerf_hardware:=false", "use_ros2_control:=false"),
]


@pytest.mark.parametrize("args", VARIANTS, ids=lambda a: " ".join(a))
def test_variant_renders_and_has_stable_names(args):
    """Jede Variante rendert; Basis-Links/-Joints sind vollstaendig."""
    root = ET.fromstring(render(*args))
    joints = {j.get("name") for j in root.findall("joint")}
    links = {li.get("name") for li in root.findall("link")}
    assert BASE_JOINTS <= joints, f"fehlende Joints: {BASE_JOINTS - joints}"
    assert BASE_LINKS <= links, f"fehlende Links: {BASE_LINKS - links}"
    if "use_depth_camera:=true" in args:
        assert "depth_camera_link" in links
        assert "depth_camera_joint" in joints
        assert "depth_camera_link_optical" in links


@pytest.mark.parametrize(
    "sim_mode,expected_name",
    [("true", "GubotIgnitionSystem"), ("false", "RealRobot")],
)
def test_ros2_control_block(sim_mode, expected_name):
    """ros2_control-Name und die 10 IMU-Interfaces pro Variante."""
    root = ET.fromstring(
        render(f"sim_mode:={sim_mode}", "use_nerf_hardware:=false")
    )
    blocks = {rc.get("name"): rc for rc in root.findall("ros2_control")}
    assert expected_name in blocks, f"ros2_control {expected_name} fehlt"
    sensor = blocks[expected_name].find("sensor[@name='imu_sensor']")
    assert sensor is not None, "imu_sensor fehlt im ros2_control-Block"
    declared = [si.get("name") for si in sensor.findall("state_interface")]
    assert declared == IMU_INTERFACES
    # Alle 4 Rad-Joints deklariert
    joint_names = {j.get("name") for j in blocks[expected_name].findall("joint")}
    assert {
        "fl_wheel_joint", "fr_wheel_joint", "rl_wheel_joint", "rr_wheel_joint"
    } <= joint_names


def test_sim_wheel_friction_fdir1():
    """Mecanum-fdir1-Vektoren (X-Anordnung) nur in der Sim-Variante."""
    sim = render("sim_mode:=true", "use_nerf_hardware:=false")
    expected = {
        "fl_wheel_link": "1 -1 0",
        "fr_wheel_link": "1 1 0",
        "rl_wheel_link": "1 1 0",
        "rr_wheel_link": "1 -1 0",
    }
    root = ET.fromstring(sim)
    found = {}
    for gz in root.findall("gazebo"):
        ref = gz.get("reference")
        fdir = gz.find(".//fdir1")
        if ref in expected and fdir is not None:
            found[ref] = fdir.text.strip()
    assert found == expected, f"fdir1-Vektoren falsch: {found}"

    # Hardware-Variante enthaelt keine Gazebo-Reibungsbloecke
    hw = render("sim_mode:=false", "use_nerf_hardware:=false")
    assert "<fdir1" not in hw, "fdir1 darf nur in der Sim-Variante vorkommen"
    assert "imu/data_raw" not in hw, (
        "Gazebo-IMU-Sensor darf nur in der Sim-Variante vorkommen"
    )


@pytest.mark.parametrize("sim_mode", ["true", "false"])
def test_check_urdf(sim_mode):
    """Rendered URDF ist fuer den URDF-Parser gueltig (check_urdf)."""
    if shutil.which("check_urdf") is None:
        pytest.skip("check_urdf nicht installiert")
    urdf = render(f"sim_mode:={sim_mode}", "use_nerf_hardware:=false")
    with tempfile.NamedTemporaryFile("w", suffix=".urdf") as f:
        f.write(urdf)
        f.flush()
        result = subprocess.run(
            ["check_urdf", f.name], capture_output=True, text=True
        )
    assert result.returncode == 0, f"check_urdf failed: {result.stderr}"


def test_wheel_geometry_consistent_with_controllers_yaml():
    """Drift-Wache: controllers.yaml == config/robot_dimensions.yaml."""
    dims = yaml.safe_load(open(DIMENSIONS_YAML))
    controllers = yaml.safe_load(open(CONTROLLERS_YAML))
    params = controllers["/**"]["mecanum_drive_controller"]["ros__parameters"]
    assert params["wheel_separation_x"] == pytest.approx(
        2 * dims["wheel_offset_x"]
    ), "wheel_separation_x != 2 * wheel_offset_x (robot_dimensions.yaml)"
    assert params["wheel_separation_y"] == pytest.approx(
        2 * dims["wheel_offset_y"]
    ), "wheel_separation_y != 2 * wheel_offset_y (robot_dimensions.yaml)"
    assert params["wheel_radius"] == pytest.approx(
        dims["wheel_radius"]
    ), "wheel_radius weicht von robot_dimensions.yaml ab"


def test_urdf_wheel_positions_match_dimensions_yaml():
    """Die gerenderten Rad-Joint-Origins entsprechen robot_dimensions.yaml."""
    dims = yaml.safe_load(open(DIMENSIONS_YAML))
    root = ET.fromstring(render("sim_mode:=true", "use_nerf_hardware:=false"))
    joints = {j.get("name"): j for j in root.findall("joint")}
    fl = joints["fl_wheel_joint"].find("origin").get("xyz").split()
    assert float(fl[0]) == pytest.approx(dims["wheel_offset_x"])
    assert float(fl[1]) == pytest.approx(dims["wheel_offset_y"])
