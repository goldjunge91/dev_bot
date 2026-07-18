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
Konsistenztests fuer die EKF-Konfiguration (robot_localization).

Sichern den Topic-/Frame-Kontrakt: Mecanum-Odom -> odometry/wheels,
IMU-Broadcaster -> imu/data, Frames base_link/odom/map.
"""

from pathlib import Path

import pytest
import yaml

CONFIG = Path(__file__).resolve().parents[1] / "config" / "ekf.yaml"


@pytest.fixture(scope="module")
def ekf_params():
    """Laedt die ros__parameters des ekf_node."""
    with open(CONFIG) as f:
        data = yaml.safe_load(f)
    return data["/**"]["ekf_node"]["ros__parameters"]


def test_config_parses(ekf_params):
    """Die Datei ist gueltiges YAML mit ekf_node-Parametern."""
    assert isinstance(ekf_params, dict)
    assert ekf_params["frequency"] > 0.0


def test_frames(ekf_params):
    """Frames entsprechen dem Projektstandard."""
    assert ekf_params["map_frame"] == "map"
    assert ekf_params["odom_frame"] == "odom"
    assert ekf_params["base_link_frame"] == "base_link"


def test_world_frame_is_odom(ekf_params):
    """EKF publiziert odom->base_link (kein map-EKF)."""
    assert ekf_params["world_frame"] == ekf_params["odom_frame"]


def test_two_d_mode_and_tf(ekf_params):
    """Planarer Roboter: 2D-Modus an, TF wird publiziert."""
    assert ekf_params["two_d_mode"] is True
    assert ekf_params["publish_tf"] is True


def test_odom_input_topic(ekf_params):
    """odom0 kommt vom Mecanum-Controller (odometry/wheels)."""
    assert ekf_params["odom0"] == "odometry/wheels"


def test_imu_input_topic(ekf_params):
    """imu0 kommt vom IMU-Broadcaster-Remap (imu/data)."""
    assert ekf_params["imu0"] == "imu/data"


def test_sensor_config_vectors(ekf_params):
    """Beide Sensor-Configs haben 15 Boolean-Eintraege."""
    for key in ("odom0_config", "imu0_config"):
        config = ekf_params[key]
        assert len(config) == 15
        assert all(isinstance(v, bool) for v in config)


def test_process_noise_covariance_is_15x15(ekf_params):
    """Die Prozessrausch-Kovarianz hat 225 Eintraege (15x15)."""
    cov = ekf_params["process_noise_covariance"]
    assert len(cov) == 225
    # PyYAML parst "5e-3" als String — rcl akzeptiert es; hier reicht,
    # dass jeder Eintrag numerisch interpretierbar ist.
    assert all(float(v) >= 0.0 for v in cov)
