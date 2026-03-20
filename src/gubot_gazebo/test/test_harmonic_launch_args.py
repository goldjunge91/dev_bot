"""Regression tests for Gazebo Harmonic (Ignition) launch wiring."""


def test_simulation_launch_declares_launch_joystick_arg_default_false():
    """simulation.launch.py muss launch_joystick deklarieren (default false)."""
    with open(
        "src/gubot_gazebo/launch/simulation.launch.py",
        encoding="utf-8",
    ) as file_handle:
        content = file_handle.read()

    assert '"launch_joystick"' in content, (
        "simulation.launch.py deklariert kein launch_joystick-Argument"
    )
    assert 'default_value="false"' in content, (
        "launch_joystick ist nicht standardmäßig deaktiviert"
    )
    assert '"launch_joystick": launch_joystick' in content, (
        "simulation.launch.py reicht launch_joystick nicht an spawn_robot weiter"
    )


def test_spawn_robot_joystick_is_conditional():
    """spawn_robot.launch.py darf joystick.launch.py nur konditional starten."""
    with open(
        "src/gubot_gazebo/launch/spawn_robot.launch.py",
        encoding="utf-8",
    ) as file_handle:
        content = file_handle.read()

    assert "declare_launch_joystick_cmd" in content, (
        "spawn_robot.launch.py deklariert launch_joystick nicht"
    )
    assert 'default_value="false"' in content, (
        "spawn_robot.launch.py setzt launch_joystick nicht default=false"
    )
    assert "condition=IfCondition(launch_joystick)" in content, (
        "joystick.launch.py wird in spawn_robot.launch.py nicht konditional gestartet"
    )
