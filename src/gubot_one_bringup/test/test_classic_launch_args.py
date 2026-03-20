"""Regression tests for Gazebo Classic launch and URDF wiring."""

import subprocess


def test_robot_classic_urdf_xacro_valid():
    """robot_classic.urdf.xacro muss zu gültigem URDF prozessiert werden können."""
    result = subprocess.run(
        [
            "ros2",
            "run",
            "xacro",
            "xacro",
            "src/gubot_one_description/description/robot_classic.urdf.xacro",
            "integrated_mode:=true",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"xacro fehlgeschlagen:\n{result.stderr}"
    assert "<robot" in result.stdout, "URDF enthält kein <robot>-Element"
    assert "gazebo_ros2_control/GazeboSystem" in result.stdout, (
        "Classic-URDF lädt nicht das richtige ros2_control-Plugin"
    )
    assert "gz_ros2_control/GazeboSimSystem" not in result.stdout, (
        "Classic-URDF lädt fälschlicherweise das Ignition-Plugin"
    )


def test_classic_camera_plugin_present():
    """robot_classic.urdf.xacro muss libgazebo_ros_camera.so einbinden."""
    result = subprocess.run(
        [
            "ros2",
            "run",
            "xacro",
            "xacro",
            "src/gubot_one_description/description/robot_classic.urdf.xacro",
            "integrated_mode:=true",
        ],
        capture_output=True,
        text=True,
    )
    assert "libgazebo_ros_camera.so" in result.stdout, (
        "Kein libgazebo_ros_camera.so in Classic-URDF gefunden"
    )


def test_classic_config_path_correct():
    """gz_classic_ros2_control.xacro darf nicht auf gubot_one/config zeigen."""
    with open(
        "src/gubot_one_description/description/gz_classic_ros2_control.xacro",
        encoding="utf-8",
    ) as file_handle:
        content = file_handle.read()

    assert "$(find gubot_one)/config" not in content, (
        "Falscher Config-Pfad: $(find gubot_one)/config gefunden"
    )
    assert "$(find gubot_one_bringup)/config" in content, (
        "Korrekter Config-Pfad $(find gubot_one_bringup)/config fehlt"
    )


def test_gubot_gazebo_classic_launch_uses_integrated_mode():
    """Classic-Launch muss integrated_mode:=true an rsp_classic übergeben."""
    with open(
        "src/gubot_gazebo/launch/gz_classic_launch_sim.launch.py",
        encoding="utf-8",
    ) as file_handle:
        content = file_handle.read()

    assert '"rsp_classic.launch.py"' in content, (
        "gubot_gazebo Classic-Launch nutzt nicht rsp_classic.launch.py"
    )
    assert '"integrated_mode": "true"' in content, (
        "gubot_gazebo Classic-Launch setzt integrated_mode nicht auf true"
    )
