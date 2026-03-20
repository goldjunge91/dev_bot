"""Integration test: Classic sim + nerf_teleop should move the robot."""

import os
import signal
import subprocess
import time

import pytest
import rclpy
from nav_msgs.msg import Odometry

RUN_GAZEBO_INTEGRATION_TESTS = (
    os.environ.get("RUN_GAZEBO_INTEGRATION_TESTS", "0") == "1"
)

pytestmark = pytest.mark.skipif(
    not RUN_GAZEBO_INTEGRATION_TESTS,
    reason=(
        "Set RUN_GAZEBO_INTEGRATION_TESTS=1 to run Gazebo Classic integration tests."
    ),
)


class _OdomCollector:
    def __init__(self, node):
        self.samples = []
        self._sub_odom = node.create_subscription(
            Odometry,
            "/odom",
            self._callback,
            20,
        )
        self._sub_diff_odom = node.create_subscription(
            Odometry,
            "/diff_cont/odom",
            self._callback,
            20,
        )

    def _callback(self, msg):
        self.samples.append(
            (
                time.time(),
                float(msg.pose.pose.position.x),
                float(msg.pose.pose.position.y),
            )
        )


def _terminate_process(proc):
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _wait_until(predicate, timeout_sec, poll_sec=0.2):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(poll_sec)
    return False


def _controllers_ready():
    cmd = (
        "source install/setup.bash && "
        "ros2 control list_controllers --controller-manager /controller_manager"
    )
    result = subprocess.run(
        ["bash", "-lc", cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    out = (result.stdout or "") + "\n" + (result.stderr or "")
    return (
        "joint_broad" in out
        and "diff_cont" in out
        and "active" in out
    )


def test_classic_sim_with_nerf_teleop_moves_robot():
    """Start Classic sim + nerf_teleop and verify odometry changes."""
    launch_proc = None
    teleop_proc = None

    try:
        launch_cmd = (
            "source install/setup.bash && "
            "ros2 launch gubot_gazebo gz_classic_launch_sim.launch.py "
            "use_nerf_hardware:=true launch_joystick:=false use_rviz:=false gui:=false"
        )
        launch_proc = subprocess.Popen(
            ["bash", "-lc", launch_cmd],
            cwd="/home/ros/projects/my_new_robot",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        assert _wait_until(_controllers_ready, timeout_sec=60), (
            "Controller manager wurde nicht rechtzeitig aktiv "
            "(joint_broad/diff_cont)."
        )

        env = os.environ.copy()
        env["NERF_TELEOP_TEST_MODE"] = "1"
        env["NERF_TELEOP_TEST_KEYS"] = "wwwwwwwwwwwwwwwwwwww"

        teleop_proc = subprocess.Popen(
            ["bash", "-lc", "source install/setup.bash && ros2 run gubot_one_bringup nerf_teleop.py"],
            cwd="/home/ros/projects/my_new_robot",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        rclpy.init()
        node = rclpy.create_node("test_classic_nerf_teleop_movement")
        collector = _OdomCollector(node)

        start = time.time()
        while time.time() - start < 8.0:
            rclpy.spin_once(node, timeout_sec=0.1)

        assert collector.samples, "Keine Odom-Daten empfangen (/odom oder /diff_cont/odom)."

        x_values = [sample[1] for sample in collector.samples]
        y_values = [sample[2] for sample in collector.samples]
        dx = max(x_values) - min(x_values)
        dy = max(y_values) - min(y_values)

        assert dx > 0.05 or dy > 0.05, (
            "Robot-Bewegung nicht nachweisbar: "
            f"dx={dx:.4f}, dy={dy:.4f}, samples={len(collector.samples)}"
        )

    finally:
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass

        _terminate_process(teleop_proc)
        _terminate_process(launch_proc)
