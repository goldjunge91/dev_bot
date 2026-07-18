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
Konsistenztests fuer die Gazebo-Bridge- und World-Konfiguration.

Sichern den Topic-Kontrakt zwischen URDF-Sensoren, ros_gz_bridge und
den EKF-Eingaengen sowie die Ladbarkeit der Launch-Dateien.
"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

PKG = Path(__file__).resolve().parents[1]
DESCRIPTION_URDF = PKG.parent / "gubot_description" / "urdf"
EKF_YAML = PKG.parent / "gubot_localization" / "config" / "ekf.yaml"


@pytest.fixture(scope="module")
def robot_bridge():
    """Laedt die Per-Robot-Bridge (gubot_bridge.yaml)."""
    with open(PKG / "config" / "gubot_bridge.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def clock_bridge():
    """Laedt die globale Bridge (gz_bridge.yaml)."""
    with open(PKG / "config" / "gz_bridge.yaml") as f:
        return yaml.safe_load(f)


def test_clock_bridge_exact(clock_bridge):
    """Globale Bridge enthaelt genau den /clock-Eintrag."""
    assert clock_bridge == [
        {
            "topic_name": "/clock",
            "ros_type_name": "rosgraph_msgs/msg/Clock",
            "gz_type_name": "gz.msgs.Clock",
            "direction": "GZ_TO_ROS",
        }
    ]


def test_robot_bridge_topic_set(robot_bridge):
    """Per-Robot-Bridge bridgt exakt die erwarteten Topics."""
    topics = {entry["topic_name"] for entry in robot_bridge}
    assert topics == {
        "scan",
        "camera/camera_info",
        "camera/image_raw",
        "imu/data_raw",
        "/model/gubot_one/cmd_vel",
    }


def test_robot_bridge_types_and_direction(robot_bridge):
    """Alle Eintraege sind GZ_TO_ROS mit passenden Message-Typen."""
    expected_types = {
        "scan": ("sensor_msgs/msg/LaserScan", "gz.msgs.LaserScan"),
        "camera/camera_info": ("sensor_msgs/msg/CameraInfo", "gz.msgs.CameraInfo"),
        "camera/image_raw": ("sensor_msgs/msg/Image", "gz.msgs.Image"),
        "imu/data_raw": ("sensor_msgs/msg/Imu", "gz.msgs.IMU"),
        "/model/gubot_one/cmd_vel": ("geometry_msgs/msg/Twist", "gz.msgs.Twist"),
    }
    for entry in robot_bridge:
        ros_type, gz_type = expected_types[entry["topic_name"]]
        assert entry["ros_type_name"] == ros_type
        assert entry["gz_type_name"] == gz_type
        assert entry["direction"] == "GZ_TO_ROS"


def _urdf_sensor_topics():
    """Sammelt alle <topic>-Tags aus den Sensor-/Sim-Xacros."""
    topics = set()
    for xacro_file in DESCRIPTION_URDF.glob("*.xacro"):
        root = ET.parse(xacro_file).getroot()
        for topic in root.iter("topic"):
            topics.add(topic.text.strip())
    return topics


def test_bridged_sensor_topics_exist_in_urdf(robot_bridge):
    """Jedes gebridgte Sensor-Topic ist ein URDF-<topic>-Tag."""
    urdf_topics = _urdf_sensor_topics()
    # camera_info publiziert der gz-Kamerasensor implizit neben image_raw;
    # cmd_vel ist kein Sensor-Topic.
    implicit = {"camera/camera_info", "/model/gubot_one/cmd_vel"}
    for entry in robot_bridge:
        topic = entry["topic_name"]
        if topic in implicit:
            continue
        assert topic in urdf_topics, (
            f"Bridge-Topic {topic} hat kein URDF-<topic>-Tag"
        )


def test_ekf_inputs_match_ros2_control_remaps():
    """EKF-Eingaenge entsprechen den ros2_control-Remappings im URDF."""
    with open(EKF_YAML) as f:
        ekf = yaml.safe_load(f)["/**"]["ekf_node"]["ros__parameters"]
    gz_control = (
        DESCRIPTION_URDF / "ros2_control_gazebo_ign_fortress.xacro"
    ).read_text()
    assert f"mecanum_drive_controller/odom:={ekf['odom0']}" in gz_control
    assert f"imu_broadcaster/imu:={ekf['imu0']}" in gz_control


@pytest.mark.parametrize("world", ["empty.world", "obstacles.world"])
def test_worlds_parse_as_xml(world):
    """Die World-Dateien sind gueltiges SDF-XML."""
    root = ET.parse(PKG / "worlds" / world).getroot()
    assert root.tag == "sdf"
    assert root.find("world") is not None


@pytest.mark.parametrize(
    "launch_file", ["simulation.launch.py", "spawn_robot.launch.py"]
)
def test_launch_files_show_args(launch_file):
    """Launch-Files laden fehlerfrei (--show-args)."""
    result = subprocess.run(
        ["ros2", "launch", str(PKG / "launch" / launch_file), "--show-args"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"{launch_file} laedt nicht:\n{result.stderr}"
    )
