# Copyright 2026 gubot_one contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Phase 2 – Struktur-Test für nerf_launch_system.

nerf_launch_system ist ein Hardware-Interface-Paket (ros2_control Plugin + Firmware).
Simulation-Welten gehören zentral nach gubot_gazebo/worlds/ –
getrennt nach Gazebo-Version (Classic / Ignition).
"""

import os
import re
import pytest

NLS_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_no_active_worlds_folder():
    """nerf_launch_system/worlds/ darf keine aktiven World-Dateien enthalten.

    Worlds wurden nach gubot_gazebo/worlds/ überführt:
      empty_ignition_standalone.world  (Ignition, standalone Launcher-Test)
      obstacles_classic.world          (Classic, konsolidiert)
    """
    worlds_path = os.path.join(NLS_ROOT, "worlds")
    if not os.path.isdir(worlds_path):
        return  # Ordner bereits entfernt – Test besteht
    active = [
        f for f in os.listdir(worlds_path)
        if f.endswith(".world") and not f.endswith(".disabled")
    ]
    assert active == [], (
        f"nerf_launch_system/worlds/ enthält noch aktive World-Dateien: {active}\n"
        "Bitte nach gubot_gazebo/worlds/ überführen und Referenzen in "
        "simulate.launch.py aktualisieren."
    )


def test_simulate_launch_uses_gubot_gazebo_worlds():
    """simulate.launch.py muss gubot_gazebo für Worlds referenzieren."""
    launch_file = os.path.join(NLS_ROOT, "launch", "simulate.launch.py")
    if not os.path.exists(launch_file):
        pytest.skip("simulate.launch.py nicht gefunden")
    content = open(launch_file).read()
    assert '"nerf_launch_system"' not in content or "worlds" not in content.split(
        '"nerf_launch_system"'
    )[1].split("\n")[0], (
        "simulate.launch.py referenziert noch nerf_launch_system für worlds. "
        "Bitte auf gubot_gazebo umstellen."
    )


def _extract_publish_rate(yaml_content):
    """Extrahiert publish_rate robust aus dem minimalistischen YAML-Inhalt."""
    match = re.search(r"publish_rate:\s*([0-9]+(?:\.[0-9]+)?)", yaml_content)
    assert match is not None, "publish_rate fehlt in gazebo_params.yaml"
    return float(match.group(1))


def test_nerf_gazebo_params_is_intentionally_distinct_from_bringup():
    """Standalone-NERF nutzt bewusst andere Gazebo-Rate als bringup.

    Phase 2 Schritt 2.4: Datei NICHT deaktivieren/löschen, da kein Duplikat.
    """
    nerf_params = os.path.join(NLS_ROOT, "config", "gazebo_params.yaml")
    bringup_params = os.path.join(
        NLS_ROOT, "..", "gubot_one_bringup", "config", "gazebo_params.yaml"
    )

    assert os.path.exists(nerf_params), "nerf_launch_system/config/gazebo_params.yaml fehlt"
    assert os.path.exists(bringup_params), "gubot_one_bringup/config/gazebo_params.yaml fehlt"

    nerf_rate = _extract_publish_rate(open(nerf_params).read())
    bringup_rate = _extract_publish_rate(open(bringup_params).read())

    assert nerf_rate != bringup_rate, (
        "gazebo_params.yaml ist identisch geworden, obwohl Standalone-NERF bewusst "
        "eine eigene publish_rate nutzt."
    )
    assert nerf_rate == 100.0, "Erwartete Standalone-NERF publish_rate ist 100.0"
    assert bringup_rate == 400.0, "Erwartete bringup publish_rate ist 400.0"
