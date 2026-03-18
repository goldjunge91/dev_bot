#!/usr/bin/env python3
"""Extended probe: Find ALL publishers on cmd/command topics + measure deltas"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time
import sys

class ExtendedProbeNode(Node):
    def __init__(self):
        super().__init__('extended_probe_node')
        self.joint_data = {}
        self.samples = []
        self.start_time = None
        
        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_callback,
            qos_profile_value=10
        )
    
    def joint_callback(self, msg):
        self.samples.append(msg)
        for name, pos in zip(msg.name, msg.position):
            if name not in self.joint_data:
                self.joint_data[name] = {'initial': pos, 'samples': []}
            self.joint_data[name]['samples'].append(pos)
    
    def find_all_publishers(self):
        """Find all active publishers on topics with 'cmd', 'command', 'vel' in name"""
        all_topics = self.get_topic_names_and_types()
        cmd_topics = [t[0] for t in all_topics if any(k in t[0].lower() for k in ['cmd', 'command', 'vel'])]
        
        print("\n=== ALL COMMAND-LIKE TOPICS ===")
        for topic in sorted(cmd_topics):
            infos = self.get_publishers_info_by_topic(topic)
            pubs = [f"{i.node_namespace}/{i.node_name}".replace('//', '/') for i in infos]
            print(f"{topic}: {pubs if pubs else 'EMPTY'}")
        
        return cmd_topics

def main():
    rclpy.init()
    node = ExtendedProbeNode()
    
    print("=== EXTENDED PROBE ===")
    print("Searching for all command topics...")
    time.sleep(1)  # Wait for initial subscriptions
    
    cmd_topics = node.find_all_publishers()
    
    print("\n=== MEASURING JOINT STATE FOR 15s ===")
    start = time.time()
    while (time.time() - start) < 15:
        rclpy.spin_once(node, timeout_sec=0.1)
    
    print(f"\nTotal samples collected: {len(node.samples)}")
    
    print("\n=== JOINT DELTAS ===")
    for name in sorted(node.joint_data.keys()):
        data = node.joint_data[name]
        if len(data['samples']) > 1:
            initial = data['initial']
            final = data['samples'][-1]
            delta = final - initial
            max_pos = max(data['samples'])
            min_pos = min(data['samples'])
            print(f"{name}:")
            print(f"  initial={initial:.6f}, final={final:.6f}, delta={delta:.6f}")
            print(f"  range=[{min_pos:.6f} to {max_pos:.6f}], spread={max_pos-min_pos:.6f}")
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
