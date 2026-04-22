"""
Test: launch_robot.launch.py — Mecanum Konfiguration.

Prueft gemaess Plan 01:
- Die Controller-Manager Konfiguration muss 'my_controllers.yaml' laden.
- Der Spawner muss 'mecanum_cont' starten.
- Das twist_mux Remapping muss auf '/mecanum_cont/cmd_vel_unstamped' zeigen.

Ansatz: Kombination aus Textanalyse (zuverlaessig) und LaunchDescription
Introspection.
"""

import os
import importlib.util

from launch import LaunchContext
from launch.actions import DeclareLaunchArgument

# Pfad relativ zu diesem Test-Skript (../launch/launch_robot.launch.py)
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_LAUNCH_FILE = os.path.join(
    _TEST_DIR, "..", "launch", "launch_robot.launch.py"
)


def _load_launch_source():
    """Laedt den Quelltext der Launch-Datei."""
    with open(_LAUNCH_FILE) as f:
        return f.read()


def _load_launch_description():
    """Laedt die LaunchDescription aus launch_robot.launch.py."""
    spec = importlib.util.spec_from_file_location("launch_robot", _LAUNCH_FILE)
    launch_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launch_mod)
    return launch_mod.generate_launch_description()


def test_launch_arguments():
    """Prueft ob Launch-Argumente vorhanden sind."""
    ld = _load_launch_description()

    found_nerf = False
    for action in ld.entities:
        if (isinstance(action, DeclareLaunchArgument)
                and action.name == 'use_nerf_hardware'):
            found_nerf = True
            break
    assert found_nerf, "Launch-Argument 'use_nerf_hardware' fehlt"


def test_controller_configuration():
    """Prueft ob mecanum_cont Spawner und YAML konfiguriert sind."""
    source = _load_launch_source()

    # my_controllers.yaml muss referenziert werden
    assert 'my_controllers.yaml' in source, (
        "my_controllers.yaml wird nicht in launch_robot referenziert"
    )

    # mecanum_cont Spawner muss vorhanden sein (nicht auskommentiert)
    # Suche nach aktiver (nicht auskommentierter) Zeile
    active_lines = [
        line.strip() for line in source.splitlines()
        if not line.strip().startswith('#')
    ]
    active_source = '\n'.join(active_lines)

    assert 'mecanum_cont' in active_source, (
        "Spawner fuer mecanum_cont fehlt in aktiven Zeilen"
    )

    # diff_cont darf nicht in aktiven Zeilen vorkommen
    # (auskommentierte ALT-Zeilen sind OK)
    diff_cont_active = any(
        'diff_cont' in line and 'arguments' in line
        for line in active_lines
    )
    assert not diff_cont_active, (
        "Spawner fuer diff_cont ist noch in aktiver Konfiguration"
    )


def test_twist_mux_remap():
    """Prueft das Remapping von twist_mux auf mecanum_cont."""
    source = _load_launch_source()

    # Suche in aktiven (nicht auskommentierten) Zeilen
    active_lines = [
        line.strip() for line in source.splitlines()
        if not line.strip().startswith('#')
    ]
    active_source = '\n'.join(active_lines)

    assert '/mecanum_cont/cmd_vel_unstamped' in active_source, (
        "twist_mux remap auf /mecanum_cont/cmd_vel_unstamped fehlt "
        "in aktiven Zeilen"
    )

    # ALT diff_cont remap darf nicht aktiv sein
    assert '/diff_cont/cmd_vel_unstamped' not in active_source, (
        "Altes diff_cont remap ist noch aktiv — muss auskommentiert sein"
    )
