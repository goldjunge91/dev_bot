"""Tests for verifying launch file syntax and start script behavior."""

import os
import stat
import subprocess
import tempfile

from ament_index_python.packages import get_package_share_directory

# Workspace-Root dynamisch aus der Testdatei ableiten
# ALT: workspace_dir war hartkodiert auf /home/ros/projects/my_new_robot
#      (existiert nicht — Workspace heißt my_new_robot_9e34131)
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.abspath(os.path.join(_TEST_DIR, "..", "..", ".."))


def test_launch_all_real_syntax_and_dependencies():
    """
    Test launch file syntax and dependencies.

    Testet, ob das Launch-File syntaktisch korrekt ist und alle referenzierten
    Pakete (wie face_tracker) vorhanden sind.
    """
    package_dir = get_package_share_directory("gubot_bringup")
    launch_file_path = os.path.join(
        package_dir, "launch", "launch_all_real.launch.py"
    )

    result = subprocess.run(
        ["ros2", "launch", launch_file_path, "--show-args"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Fehler im Launch-File (fehlende Pakete oder Syntaxfehler):\n{result.stderr}"
    )


def test_start_robot_sh_execution_dry_run():
    """
    Test the start_robot.sh execution using a mock ros2 command.

    Testet das start_robot.sh Skript, indem der ros2 launch Befehl durch ein
    Mock ersetzt wird. So wird sichergestellt, dass keine
    Variablen-Initialisierungsfehler (--face) mehr auftreten.
    """
    script_content = """#!/bin/bash
    source /opt/ros/humble/setup.bash

    # Fake ros2 command to prevent actual launch
    ros2() {
        if [[ "$1" == "launch" ]]; then
            echo "Mocked ros2 launch. Args: ${@}"
            return 0
        fi
        command ros2 "$@"
    }

    export -f ros2

    # Run the script with and without --face to ensure no malformed arguments
    bash ./src/gubot_utils/scripts/start_robot.sh --target schatz
    bash ./src/gubot_utils/scripts/start_robot.sh --face --target schatz
    """

    # Mock-Script innerhalb des Workspace anlegen (Projektregel: nicht nach
    # /tmp schreiben) und nach dem Test aufräumen
    # ALT: fester Pfad /tmp/test_start_robot.sh ohne Cleanup
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".sh",
        prefix="test_start_robot_",
        dir=_TEST_DIR,
        delete=False,
    ) as f:
        f.write(script_content)
        test_sh_path = f.name

    try:
        os.chmod(test_sh_path, os.stat(test_sh_path).st_mode | stat.S_IXUSR)

        result = subprocess.run(
            ["bash", test_sh_path],
            cwd=_WORKSPACE_DIR,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Fehler beim Ausführen von start_robot.sh:\n{result.stderr}"
        )
        assert "malformed launch argument" not in result.stderr, (
            "Fehler: malformed launch argument gefunden!"
        )
        assert (
            "launch_face_tracker:=false" in result.stdout
            or "launch_face_tracker:=true" in result.stdout
        )
    finally:
        os.unlink(test_sh_path)
