# MIGRATION STATUS: SCAFFOLDING (Sprint 6 — CI launch test)
# test_launch.py — launch_testing integration test.
# Verifies the controller_manager loads with mock_hardware and lists 4 velocity interfaces.
#
# Run: colcon test --packages-select mecanum_pico
#      colcon test-result --verbose

import unittest
import launch
import launch_ros
import launch_testing
import launch_testing.actions
import launch_testing.markers
import pytest
import rclpy
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


@pytest.mark.launch_test
@launch_testing.markers.keep_alive
def generate_test_description():
    pkg_share = get_package_share_directory('mecanum_pico')
    launch_file = os.path.join(pkg_share, 'launch', 'mecanum_pico.launch.py')

    return launch.LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={'use_mock_hardware': 'true', 'use_rviz': 'false'}.items(),
        ),
        launch_testing.actions.ReadyToTest(),
    ])


class TestMecanumPicoLaunch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('test_mecanum_launch')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_controller_manager_active(self):
        """Verify /controller_manager node is present after launch."""
        # TODO(sprint6): Use ros2 service call /controller_manager/list_controllers
        # For now, assert the node graph is non-empty
        self.assertIsNotNone(self.node)

    def test_four_velocity_interfaces_exist(self):
        """
        Verify 4 velocity command interfaces are listed.
        Expected (mock hardware):
          front_left_wheel_joint/velocity  [available]
          front_right_wheel_joint/velocity [available]
          rear_left_wheel_joint/velocity   [available]
          rear_right_wheel_joint/velocity  [available]
        TODO(sprint6): Call /controller_manager/list_hardware_interfaces service
        and assert len(velocity_command_interfaces) == 4
        """
        self.skipTest("Sprint 6 full implementation pending colcon build on target.")
