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
Konsistenztests fuer die Nav2- und slam_toolbox-Konfiguration.

Sichern Frames, den Odom-Topic-Kontrakt (/odometry/filtered vom EKF),
die Mecanum-Faehigkeit (Quergeschwindigkeit) und die Lidar-Reichweite
gegen die URDF-Quelle.
"""

import ast
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

PKG = Path(__file__).resolve().parents[1]
NAV2_YAML = PKG / "config" / "nav2_params.yaml"
SLAM_YAML = PKG / "config" / "slam_toolbox_params.yaml"
LIDAR_XACRO = PKG.parent / "gubot_description" / "urdf" / "sensor_lidar.xacro"


@pytest.fixture(scope="module")
def nav2():
    """Laedt nav2_params.yaml."""
    with open(NAV2_YAML) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def slam():
    """Laedt die slam_toolbox-Parameter."""
    with open(SLAM_YAML) as f:
        return yaml.safe_load(f)["slam_toolbox"]["ros__parameters"]


def _walk(node, key):
    """Sammelt rekursiv alle Werte eines Schluessels in einem Dict-Baum."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == key:
                found.append(v)
            found.extend(_walk(v, key))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk(item, key))
    return found


def _lidar_max_range():
    """Liest die maximale Lidar-Reichweite aus sensor_lidar.xacro."""
    root = ET.parse(LIDAR_XACRO).getroot()
    ranges = root.iter("range")
    for rng in ranges:
        max_el = rng.find("max")
        if max_el is not None:
            return float(max_el.text)
    raise AssertionError("Kein <range><max> in sensor_lidar.xacro gefunden")


def test_amcl_frames_and_motion_model(nav2):
    """AMCL: Projektframes + Omni-Modell (Mecanum) + /scan."""
    amcl = nav2["amcl"]["ros__parameters"]
    assert amcl["base_frame_id"] == "base_link"
    assert amcl["global_frame_id"] == "map"
    assert amcl["odom_frame_id"] == "odom"
    assert amcl["robot_model_type"] == "nav2_amcl::OmniMotionModel"
    assert amcl["scan_topic"] == "scan"


def test_all_odom_topics_use_ekf_output(nav2):
    """Jedes odom_topic zeigt auf den EKF-Ausgang /odometry/filtered."""
    topics = _walk(nav2, "odom_topic")
    assert len(topics) >= 2  # bt_navigator + controller_server
    assert all(t == "/odometry/filtered" for t in topics)


def test_costmap_frames(nav2):
    """Local Costmap laeuft in odom, Global Costmap in map."""
    local = nav2["local_costmap"]["local_costmap"]["ros__parameters"]
    glob = nav2["global_costmap"]["global_costmap"]["ros__parameters"]
    assert local["global_frame"] == "odom"
    assert glob["global_frame"] == "map"
    assert local["robot_base_frame"] == "base_link"
    assert glob["robot_base_frame"] == "base_link"


def test_costmap_observation_sources_use_scan(nav2):
    """Beide Obstacle-Layer beobachten /scan als LaserScan."""
    for costmap in ("local_costmap", "global_costmap"):
        params = nav2[costmap][costmap]["ros__parameters"]
        obstacle = params["obstacle_layer"]
        assert obstacle["observation_sources"] == "scan"
        assert obstacle["scan"]["topic"] == "/scan"
        assert obstacle["scan"]["data_type"] == "LaserScan"


def test_behavior_server_frames(nav2):
    """Behavior-Server: Recovery laeuft in odom/base_link."""
    behavior = nav2["behavior_server"]["ros__parameters"]
    assert behavior["global_frame"] == "odom"
    assert behavior["robot_base_frame"] == "base_link"


def test_dwb_is_omnidirectional(nav2):
    """DWB sampelt Quergeschwindigkeit (Mecanum-faehig)."""
    controller = nav2["controller_server"]["ros__parameters"]
    dwb = controller["FollowPath"]
    assert dwb["plugin"] == "dwb_core::DWBLocalPlanner"
    assert dwb["vy_samples"] > 1
    assert dwb["max_vel_y"] > 0.0
    assert dwb["min_vel_y"] < 0.0
    # Der Default 0.5 wuerde die Querbewegung wegfiltern
    assert controller["min_y_velocity_threshold"] < 0.01


def test_all_plugins_in_allowlist(nav2):
    """Alle Plugin-Strings gehoeren zu bekannten Nav2-Plugins."""
    allowed = {
        "dwb_core::DWBLocalPlanner",
        "nav2_controller::SimpleProgressChecker",
        "nav2_controller::SimpleGoalChecker",
        "nav2_costmap_2d::ObstacleLayer",
        "nav2_costmap_2d::InflationLayer",
        "nav2_costmap_2d::StaticLayer",
        "nav2_navfn_planner/NavfnPlanner",
        "nav2_smoother::SimpleSmoother",
        "nav2_behaviors/Spin",
        "nav2_behaviors/BackUp",
        "nav2_behaviors/DriveOnHeading",
        "nav2_behaviors/Wait",
        "nav2_behaviors/AssistedTeleop",
        "nav2_waypoint_follower::WaitAtWaypoint",
    }
    plugins = _walk(nav2, "plugin")
    assert plugins, "keine Plugin-Eintraege gefunden"
    unknown = [p for p in plugins if p not in allowed]
    assert unknown == [], f"Unbekannte Plugins: {unknown}"


def _node_names_from_launch(launch_file):
    """Extrahiert alle node_names-Listen per ast aus einem Launch-File."""
    tree = ast.parse((PKG / "launch" / launch_file).read_text())
    result = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Dict)
            and any(
                isinstance(k, ast.Constant) and k.value == "node_names"
                for k in node.keys
            )
        ):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "node_names":
                    result.append(ast.literal_eval(value))
    return result


def test_lifecycle_node_names(nav2):
    """Lifecycle-Manager verwalten genau die konfigurierten Nav2-Nodes."""
    assert _node_names_from_launch("navigation.launch.py") == [[
        "controller_server",
        "smoother_server",
        "planner_server",
        "behavior_server",
        "bt_navigator",
        "waypoint_follower",
    ]]
    assert _node_names_from_launch("localization.launch.py") == [
        ["map_server", "amcl"]
    ]
    assert _node_names_from_launch("map_saver.launch.py") == [["map_saver"]]


def test_lifecycle_nodes_have_parameters(nav2):
    """Jeder Lifecycle-Node hat einen Abschnitt in nav2_params.yaml."""
    for names in _node_names_from_launch("navigation.launch.py"):
        for name in names:
            assert name in nav2, f"{name} fehlt in nav2_params.yaml"


def test_slam_toolbox_frames_and_scan(slam):
    """slam_toolbox nutzt Projektframes und /scan."""
    assert slam["odom_frame"] == "odom"
    assert slam["map_frame"] == "map"
    assert slam["base_frame"] == "base_link"
    assert slam["scan_topic"] == "/scan"


def test_laser_ranges_match_urdf_lidar(nav2, slam):
    """AMCL- und SLAM-Laserreichweite == Lidar-<max> aus dem URDF."""
    lidar_max = _lidar_max_range()
    assert slam["max_laser_range"] == pytest.approx(lidar_max)
    amcl = nav2["amcl"]["ros__parameters"]
    assert amcl["laser_max_range"] == pytest.approx(lidar_max)
