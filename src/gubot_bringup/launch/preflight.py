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
Pre-Flight Hardware-Checks für die Real-Robot-Launches.

====================================================
Prüft VOR dem Start der Treiber, ob die erwarteten Geräte am Pi hängen,
und bricht den Launch sofort mit einer klaren Fehlermeldung ab
("... not found on expected port — found instead: ...").

Erwartete Geräte (Pfade wie in URDF/Launch konfiguriert):
  - Antrieb:  Raspberry Pi Pico   (ros2_control_hardware.xacro)
  - Nerf:     Arduino Pro Micro   (ros2_control_hardware.xacro, nerf_port)
  - Lidar:    RPLidar A1          (rplidar.launch.py, by-path = USB-Buchse!)
  - Kamera:   /dev/video0         (camera.launch.py / real_camera.launch.py)

Deaktivieren (z. B. Entwicklungs-PC ohne Hardware):
  ros2 launch gubot_bringup launch_all_real.launch.py check_hardware:=false
"""

import glob
import os

from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration

PICO_PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_50443405786ACA1C-if00"
NERF_PORT = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00"
LIDAR_PORT = (
    "/dev/serial/by-path/"
    "platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0-port0"
)
CAMERA_DEV = "/dev/video0"


def _found_devices(patterns):
    devices = []
    for pattern in patterns:
        devices.extend(sorted(glob.glob(pattern)))
    return devices


def _require_device(label, path, search_patterns, hint):
    if os.path.exists(path):
        return
    found = _found_devices(search_patterns)
    found_str = (
        "\n    ".join(found) if found else "(none — is it plugged in / powered?)"
    )
    raise RuntimeError(
        f"\n{'=' * 70}\n"
        f"PRE-FLIGHT CHECK FAILED: {label} not found on expected port.\n"
        f"  expected:      {path}\n"
        f"  found instead:\n    {found_str}\n"
        f"  hint:          {hint}\n"
        f"  skip check:    check_hardware:=false\n"
        f"{'=' * 70}"
    )


def check_pico():
    """Antriebs-Pico (Pflicht — ohne ihn startet ros2_control nicht)."""
    _require_device(
        "Drive base (Raspberry Pi Pico)",
        PICO_PORT,
        ["/dev/serial/by-id/*"],
        "Anderer Pico? Serial in ros2_control_hardware.xacro anpassen.",
    )


def check_nerf():
    """Nerf-Launcher Pro Micro (meldet sich als Arduino Leonardo)."""
    _require_device(
        "Nerf launcher (Arduino Pro Micro)",
        NERF_PORT,
        ["/dev/serial/by-id/*"],
        "USB-Kabel prüfen; Port ist nerf_port in ros2_control_hardware.xacro.",
    )


def check_lidar():
    """Lidar (RPLidar) — by-path kodiert die physische USB-Buchse am Pi."""
    _require_device(
        "Lidar (RPLidar)",
        LIDAR_PORT,
        ["/dev/serial/by-path/*", "/dev/serial/by-id/*"],
        "Lidar in die richtige USB-Buchse stecken ODER Pfad in "
        "rplidar.launch.py + preflight.py anpassen.",
    )


def check_camera():
    """USB-Kamera an /dev/video0."""
    _require_device(
        "Camera (USB)",
        CAMERA_DEV,
        ["/dev/video*"],
        "v4l2-ctl --list-devices; anderes Device? camera.launch.py anpassen.",
    )


def preflight_action(*checks):
    """OpaqueFunction, die die Checks ausführt (check_hardware:=false skipt)."""

    def _run(context):
        flag = LaunchConfiguration("check_hardware").perform(context)
        if flag.lower() != "true":
            print("[preflight] Hardware-Checks übersprungen (check_hardware:=false)")
            return []
        for check in checks:
            check()
        print(f"[preflight] {len(checks)} Hardware-Check(s) OK")
        return []

    return OpaqueFunction(function=_run)
