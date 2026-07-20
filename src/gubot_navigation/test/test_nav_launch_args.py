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
Syntax-Tests fuer alle gubot_navigation-Launch-Dateien.

`ros2 launch <datei> --show-args` laedt das Launch-File vollstaendig —
Syntaxfehler und fehlende Paket-Referenzen fallen sofort auf.
"""

import subprocess
from pathlib import Path

import pytest

LAUNCH_DIR = Path(__file__).resolve().parents[1] / "launch"

LAUNCH_FILES = [
    "localization.launch.py",
    "map_saver.launch.py",
    "nav2.launch.py",
    "navigation.launch.py",
    "record_scan.launch.py",
    "slam.launch.py",
]


@pytest.mark.parametrize("launch_file", LAUNCH_FILES)
def test_launch_file_show_args(launch_file):
    """Launch-File laedt fehlerfrei (--show-args)."""
    result = subprocess.run(
        ["ros2", "launch", str(LAUNCH_DIR / launch_file), "--show-args"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"{launch_file} laedt nicht:\n{result.stderr}"
