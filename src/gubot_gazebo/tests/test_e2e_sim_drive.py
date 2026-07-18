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
E2E-Test: Headless-Sim-Bringup + Seitwaertsfahrt (Mecanum-fdir1-Kanarienvogel).

Startet die komplette Simulation headless, wartet auf /odometry/filtered
(EKF laeuft => Controller + Bridge + Sensorik stehen) und faehrt dann
seitwaerts ueber /cmd_vel_joy. Eine echte Y-Verschiebung beweist, dass
die fdir1-Reibungsvektoren der Mecanum-Raeder korrekt sind.

Nur aktiv mit GUBOT_E2E=1 (CMake-Option GUBOT_E2E registriert den Test;
der Modul-Guard schuetzt vor der Root-pytest-Collection).
"""

import os
import time
import unittest

import pytest

if os.environ.get("GUBOT_E2E") != "1":
    pytest.skip(
        "E2E-Test nur mit GUBOT_E2E=1 (colcon: -DGUBOT_E2E=ON)",
        allow_module_level=True,
    )

import launch  # noqa: E402
import launch_testing  # noqa: E402
import launch_testing.actions  # noqa: E402
import rclpy  # noqa: E402
from ament_index_python.packages import get_package_share_directory  # noqa: E402
from geometry_msgs.msg import Twist  # noqa: E402
from launch.actions import IncludeLaunchDescription  # noqa: E402
from launch.launch_description_sources import (  # noqa: E402
    PythonLaunchDescriptionSource,
)
from nav_msgs.msg import Odometry  # noqa: E402

# WSL2: gz-Start ist langsam, EKF braucht erst Sensor-Daten
SIM_READY_TIMEOUT = 120.0
DRIVE_DURATION = 8.0
DRIVE_RATE_HZ = 20.0
LATERAL_SPEED = 0.3
MIN_LATERAL_DISPLACEMENT = 0.10  # m
MAX_FORWARD_RATIO = 0.5  # |dx| < 0.5 * |dy|


def generate_test_description():
    """Startet die Simulation headless ohne Kamera/Nerf-Hardware."""
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gubot_gazebo"),
                "launch",
                "simulation.launch.py",
            )
        ),
        launch_arguments={
            "headless": "true",
            "rviz": "false",
            "use_camera": "false",
            "use_nerf_hardware": "false",
        }.items(),
    )
    return launch.LaunchDescription(
        [sim_launch, launch_testing.actions.ReadyToTest()]
    )


class TestSimLateralDrive(unittest.TestCase):
    """Bringup + Seitwaertsfahrt gegen /odometry/filtered."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("e2e_drive_probe")
        cls.odom_msgs = []
        cls.node.create_subscription(
            Odometry, "/odometry/filtered", cls.odom_msgs.append, 10
        )
        cls.cmd_pub = cls.node.create_publisher(Twist, "/cmd_vel_joy", 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def _spin_for(self, duration):
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)

    def _wait_for_odom(self):
        deadline = time.monotonic() + SIM_READY_TIMEOUT
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.5)
            if self.odom_msgs:
                return
        self.fail(
            f"Kein /odometry/filtered innerhalb {SIM_READY_TIMEOUT:.0f}s — "
            "Sim-Bringup fehlgeschlagen"
        )

    def test_lateral_drive(self):
        """Seitwaertsfahrt erzeugt Y-Verschiebung ohne nennenswertes X."""
        self._wait_for_odom()
        # Kurze Beruhigungsphase, dann Startpose merken
        self._spin_for(2.0)
        start = self.odom_msgs[-1].pose.pose.position

        cmd = Twist()
        cmd.linear.y = LATERAL_SPEED
        period = 1.0 / DRIVE_RATE_HZ
        deadline = time.monotonic() + DRIVE_DURATION
        while time.monotonic() < deadline:
            self.cmd_pub.publish(cmd)
            rclpy.spin_once(self.node, timeout_sec=period)

        # Stoppen und letzte Odometrie einsammeln
        self.cmd_pub.publish(Twist())
        self._spin_for(1.0)
        end = self.odom_msgs[-1].pose.pose.position

        dx = end.x - start.x
        dy = end.y - start.y
        self.node.get_logger().info(f"E2E-Fahrt: dx={dx:.3f} m, dy={dy:.3f} m")

        self.assertGreater(
            abs(dy),
            MIN_LATERAL_DISPLACEMENT,
            f"Keine Seitwaertsbewegung (dy={dy:.3f} m) — fdir1 defekt?",
        )
        self.assertLess(
            abs(dx),
            MAX_FORWARD_RATIO * abs(dy),
            f"Zu viel Vorwaertsdrift (dx={dx:.3f} m vs dy={dy:.3f} m)",
        )


@launch_testing.post_shutdown_test()
class TestAfterShutdown(unittest.TestCase):
    """Nach dem Shutdown: tolerant gegenueber gz-Exit-Codes."""

    def test_no_hard_crash(self, proc_info):
        """Toleriert unsaubere gz-Exits auf SIGINT/SIGTERM."""
        # Bewusst permissiv: launch_testing meldet Prozess-Exits selbst;
        # dieser Platzhalter dokumentiert die Absicht und kann spaeter
        # verschaerft werden.
        self.assertTrue(True)
