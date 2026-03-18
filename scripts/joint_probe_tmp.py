#!/usr/bin/env python3
import rclpy
import time
from rclpy.node import Node
from sensor_msgs.msg import JointState

TARGET_TOPICS = [
    '/diff_cont/cmd_vel_unstamped',
    '/tilt_controller/commands',
    '/shooter_controller/commands',
    '/arming_controller/commands',
]
TARGET_JOINTS = [
    'left_wheel_joint',
    'right_wheel_joint',
    'tilt_joint',
    'shooter_joint',
    'system_arming_joint',
]

class ProbeNode(Node):
    def __init__(self):
        super().__init__('probe_during_run_tmp')
        self.samples = []
        self.sub = self.create_subscription(JointState, '/joint_states', self.cb, 10)

    def cb(self, msg: JointState):
        idx = {n: i for i, n in enumerate(msg.name)}
        row = {}
        for joint in TARGET_JOINTS:
            if joint in idx:
                i = idx[joint]
                p = float(msg.position[i]) if i < len(msg.position) else float('nan')
                v = float(msg.velocity[i]) if i < len(msg.velocity) else float('nan')
                row[joint] = (p, v)
        self.samples.append(row)

def main():
    rclpy.init()
    node = ProbeNode()

    print('=== PY PROBE ===')
    print('PUBLISHERS')
    for topic in TARGET_TOPICS:
        infos = node.get_publishers_info_by_topic(topic)
        pubs = [f"{i.node_namespace}/{i.node_name}".replace('//', '/') for i in infos]
        print(topic, pubs)

    start = time.time()
    while time.time() - start < 12.0:
        rclpy.spin_once(node, timeout_sec=0.2)

    print('SAMPLES', len(node.samples))
    if len(node.samples) >= 2:
        first = node.samples[0]
        last = node.samples[-1]
        print('DELTAS')
        for joint in TARGET_JOINTS:
            if joint in first and joint in last:
                dp = last[joint][0] - first[joint][0]
                print(joint, f'dpos={dp:.6f}', f'last_vel={last[joint][1]:.6f}')

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
