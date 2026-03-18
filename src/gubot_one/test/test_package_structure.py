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
Phase 1 – Strukturtest: gubot_one darf nur Metadaten enthalten.

gubot_one ist das Wurzelpaket und darf keine XACRO-Beschreibungen
oder Launch-Dateien enthalten. Diese gehören ausschließlich nach
gubot_one_description bzw. gubot_one_bringup.
"""

import os
import pytest

GUBOT_ONE_SRC = os.path.join(os.path.dirname(__file__), "..")


def test_no_xacro_files_in_gubot_one():
    """gubot_one darf keinen description/-Ordner mit XACRO-Dateien enthalten."""
    desc_path = os.path.join(GUBOT_ONE_SRC, "description")
    xacro_files = []
    if os.path.isdir(desc_path):
        xacro_files = [f for f in os.listdir(desc_path) if f.endswith(".xacro")]
    assert xacro_files == [], (
        f"gubot_one/description/ enthält noch XACRO-Dateien: {xacro_files}\n"
        "Kanonische Versionen liegen in gubot_one_description/description/"
    )


def test_no_launch_files_in_gubot_one():
    """gubot_one darf keinen launch/-Ordner mit Launch-Dateien enthalten."""
    launch_path = os.path.join(GUBOT_ONE_SRC, "launch")
    launch_files = []
    if os.path.isdir(launch_path):
        launch_files = [f for f in os.listdir(launch_path) if f.endswith(".py")]
    assert launch_files == [], (
        f"gubot_one/launch/ enthält noch Launch-Dateien: {launch_files}\n"
        "Kanonische Versionen liegen in gubot_one_bringup/launch/"
    )


def test_required_metafiles_present():
    """package.xml, CMakeLists.txt und .repos-Dateien müssen vorhanden sein."""
    required = ["package.xml", "CMakeLists.txt",
                "gubot_hardware.repos", "gubot_simulation.repos"]
    for f in required:
        assert os.path.isfile(os.path.join(GUBOT_ONE_SRC, f)), (
            f"Pflichtdatei fehlt in gubot_one: {f}"
        )
