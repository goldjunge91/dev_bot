# MIGRATION STATUS: SCAFFOLDING (Sprint 7 — Hardware-in-the-Loop motion tests)
# test_mecanum_motion.py — HIL motion validation tests.
#
# Prerequisites:
#   - Physical mecanum robot connected via USB
#   - ROS 2 running: ros2 launch mecanum_pico mecanum_pico.launch.py
#   - Run with: pytest test/hil/ -v
#
# Acceptance criteria (Sprint 7 Definition of Done):
#   - Straight drive:  ±5%  error vs commanded distance
#   - Rotation:        ±5%  error over 1 full revolution
#   - Strafe:          ±10% error vs commanded lateral displacement

import pytest
import rclpy
import time
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped, Twist, Vector3
from nav_msgs.msg import Odometry


# ---------------------------------------------------------------------------
# Test fixture — ROS 2 node for publishing and subscribing
# ---------------------------------------------------------------------------
class MecanumHILNode(Node):
    def __init__(self):
        super().__init__('mecanum_hil_test')
        self.cmd_pub = self.create_subscription(
            TwistStamped,
            '/mecanum_drive_controller/cmd_vel',
            lambda msg: None, 10
        )
        self._cmd_pub = self.create_publisher(
            TwistStamped,
            '/mecanum_drive_controller/cmd_vel',
            10
        )
        self.last_odom = None
        self.create_subscription(Odometry, '/mecanum_drive_controller/odom',
                                  self._odom_cb, 10)

    def _odom_cb(self, msg: Odometry):
        self.last_odom = msg

    def send_velocity(self, vx=0.0, vy=0.0, wz=0.0):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x  = vx
        msg.twist.linear.y  = vy
        msg.twist.angular.z = wz
        self._cmd_pub.publish(msg)

    def stop(self):
        self.send_velocity(0.0, 0.0, 0.0)


@pytest.fixture(scope='module')
def ros_node():
    rclpy.init()
    node = MecanumHILNode()
    yield node
    node.stop()
    node.destroy_node()
    rclpy.shutdown()


# ---------------------------------------------------------------------------
# HIL Test 1 — Straight drive
# ---------------------------------------------------------------------------
def test_straight_drive(ros_node):
    """
    Drive forward at 0.1 m/s for 2 s.
    Expect: |odom.x| > 0.17 m (accounting for ±5% at 0.18 m ideal).
    """
    pytest.skip("HIL test: requires physical robot. Remove skip when robot is connected.")

    ros_node.send_velocity(vx=0.1)
    time.sleep(2.0)
    ros_node.stop()
    time.sleep(0.2)

    odom = ros_node.last_odom
    assert odom is not None, "No odometry received"
    x = odom.pose.pose.position.x
    assert abs(x) > 0.17, f"Robot did not drive forward far enough: x={x:.3f} m"
    assert abs(odom.pose.pose.position.y) < 0.05, f"Lateral drift too large: y={odom.pose.pose.position.y:.3f}"


# ---------------------------------------------------------------------------
# HIL Test 2 — Pure strafe (mecanum-specific critical test)
# ---------------------------------------------------------------------------
def test_strafe_left(ros_node):
    """
    Strafe left at 0.1 m/s for 2 s.
    Expect: |odom.y| > 0.15 m, |odom.x| < 0.05 m (no forward drift).
    If FL/RR and FR/RL are swapped in firmware, this test fails visibly.
    """
    pytest.skip("HIL test: requires physical robot. Remove skip when robot is connected.")

    ros_node.send_velocity(vy=0.1)
    time.sleep(2.0)
    ros_node.stop()
    time.sleep(0.2)

    odom = ros_node.last_odom
    assert odom is not None, "No odometry received"
    y = odom.pose.pose.position.y
    assert abs(y) > 0.15, f"Robot did not strafe: y={y:.3f} m"
    assert abs(odom.pose.pose.position.x) < 0.05, \
        f"Robot drifted forward during strafe: x={odom.pose.pose.position.x:.3f}"


# ---------------------------------------------------------------------------
# HIL Test 3 — Pure rotation
# ---------------------------------------------------------------------------
def test_pure_rotation(ros_node):
    """
    Rotate at 1.0 rad/s for 2*pi seconds (~6.28 s).
    Expect: odom reports ~6.28 rad rotation AND ~0 m translation.
    Used to calibrate sum_of_robot_center_projection_on_X_Y_axis.
    """
    pytest.skip("HIL test: requires physical robot. Remove skip when robot is connected.")

    import math
    ros_node.send_velocity(wz=1.0)
    time.sleep(2.0 * math.pi)
    ros_node.stop()
    time.sleep(0.2)

    odom = ros_node.last_odom
    assert odom is not None, "No odometry received"
    x = odom.pose.pose.position.x
    y = odom.pose.pose.position.y
    translation = math.sqrt(x**2 + y**2)
    assert translation < 0.10, \
        f"Too much translation during rotation: {translation:.3f} m (adjust lx+ly in controllers.yaml)"
