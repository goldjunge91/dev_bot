import os
import unittest

from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions
import pytest
import rclpy
from sensor_msgs.msg import Imu


@pytest.mark.launch_test
def generate_test_description():
    """Launch the main robot bringup."""
    pkg_dir = get_package_share_directory("gubot_one")

    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, "launch", "launch_robot.launch.py")
        ),
        launch_arguments={
            "use_sim_time": "false",
            "sim_mode": "false",
            "use_fake_hardware": "true",
            "integrated_mode": "true",
            "use_nerf_hardware": "false",
            "launch_camera": "false",
            "launch_face_tracker": "false",
        }.items(),
    )

    return launch.LaunchDescription(
        [robot_launch, launch_testing.actions.ReadyToTest()]
    ), locals()


class TestImuOrientation(unittest.TestCase):
    """Test suite for verifying IMU orientation calculations."""

    @classmethod
    def setUpClass(cls):
        """Initialize ROS 2 for the test suite."""
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        """Shutdown ROS 2 after the test suite."""
        try:
            rclpy.shutdown()
        except Exception:
            pass

    def setUp(self):
        """Set up the ROS 2 node before each test."""
        self.node = rclpy.create_node("test_imu_node")
        self.msgs_rx = []

    def tearDown(self):
        """Destroy the ROS 2 node after each test."""
        if self.node is not None:
            self.node.destroy_node()

    def test_orientation_published(self, proc_output):
        """Test that /imu/data is published with actual orientation."""
        # Subscribe to the filtered topic
        self.node.create_subscription(
            Imu, "/imu/data", lambda msg: self.msgs_rx.append(msg), 10
        )

        # Wait up to 15 seconds to give the hardware controllers time to boot up
        timeout = 15.0
        start_time = self.node.get_clock().now()

        while (self.node.get_clock().now() - start_time).nanoseconds / 1e9 < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.1)

            if len(self.msgs_rx) > 0:
                msg = self.msgs_rx[0]

                # Check if it has a valid orientation (not the raw 6-DOF identity dummy)
                is_valid_quaternion = (
                    msg.orientation.x != 0.0
                    or msg.orientation.y != 0.0
                    or msg.orientation.z != 0.0
                    or msg.orientation.w != 1.0
                )

                # Assert we actually have calculated orientation
                self.assertTrue(
                    is_valid_quaternion,
                    "Orientation is still the dummy 6-DOF [0,0,0,1]",
                )
                return

        self.fail("Timeout: No message received on /imu/data")


@launch_testing.post_shutdown_test()
class TestProcessOutput(unittest.TestCase):
    def test_exit_code(self, proc_info):
        """Check that all processes in the launch exit safely."""
        # launch_testing.asserts.assertExitCodes(proc_info)
        launch_testing.asserts.assertExitCodes(proc_info, allowable_exit_codes=[0, -2])
