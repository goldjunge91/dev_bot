#!/usr/bin/env python3

# Copyright 2026 goldjunge91
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tilt Controller Debug Script.

Aufruf (waehrend simulation.launch.py laeuft):
  ws && python3 src/gubot_utils/scripts/debug_tilt.py 2>&1 | tee debug_tilt.log
"""
import sys
import time

import rclpy
from controller_manager_msgs.srv import ListControllers, ListHardwareInterfaces
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

OK = "\033[92m[OK  ]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
WARN = "\033[93m[WARN]\033[0m"
INFO = "\033[94m[INFO]\033[0m"


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


rclpy.init()
node = rclpy.create_node("debug_tilt")

# kurz warten damit Discovery laeuft
rclpy.spin_once(node, timeout_sec=1.0)

# ── 0. Simulation aktiv? ─────────────────────────────────────
section("0. Voraussetzung: Simulation laeuft?")
node_names = [n for n, _ in node.get_node_names_and_namespaces()]
if "controller_manager" not in node_names:
    print(f"  {FAIL} /controller_manager nicht gefunden")
    print(f"  Gefundene Nodes: {node_names}")
    print("  Starte zuerst: ros2 launch gubot_gazebo simulation.launch.py")
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(1)
print(f"  {OK} Simulation aktiv")

# ── 1. Nodes ─────────────────────────────────────────────────
section("1. Relevante Nodes")
for expected in ["controller_manager", "robot_state_publisher",
                 "twist_mux", "ros_gz_bridge"]:
    sym = OK if expected in node_names else FAIL
    print(f"  {sym} /{expected}")

# ── 2. Topics ────────────────────────────────────────────────
section("2. Topics")
topic_names = [t for t, _ in node.get_topic_names_and_types()]
for topic in ["/tilt_controller/commands", "/joint_states",
              "/diff_cont/cmd_vel_unstamped", "/clock"]:
    sym = OK if topic in topic_names else FAIL
    print(f"  {sym} {topic}")

# ── 3. Controller-Status via Service ─────────────────────────
section("3. Controller Manager – Status")
cli = node.create_client(
    ListControllers, "/controller_manager/list_controllers")
if not cli.wait_for_service(timeout_sec=3.0):
    print(f"  {FAIL} Service /controller_manager/list_controllers nicht erreichbar")
else:
    resp = cli.call(ListControllers.Request())
    for c in resp.controller:
        sym = OK if c.state == "active" else WARN
        print(f"  {sym} {c.name:<35} state={c.state}  type={c.type}")
    names_states = {c.name: c.state for c in resp.controller}
    for name in ["tilt_controller", "diff_cont", "joint_broad",
                 "shooter_controller", "arming_controller"]:
        if name not in names_states:
            print(f"  {FAIL} {name} FEHLT komplett")

# ── 4. Hardware Interfaces via Service ───────────────────────
section("4. Hardware Interfaces (trigger_joint/position?)")
hw_cli = node.create_client(ListHardwareInterfaces,
                            "/controller_manager/list_hardware_interfaces")
if not hw_cli.wait_for_service(timeout_sec=3.0):
    print(f"  {FAIL} Service nicht erreichbar")
else:
    hw_resp = hw_cli.call(ListHardwareInterfaces.Request())
    all_ifaces = []
    for hw in hw_resp.hardware_info:
        for c in hw.command_interfaces:
            all_ifaces.append(c.name)
            print(f"  CMD  {c.name}")
        for s in hw.state_interfaces:
            all_ifaces.append(s.name)
            print(f"  ST   {s.name}")
    sym = OK if "trigger_joint/position" in all_ifaces else FAIL
    print(f"\n  {sym} trigger_joint/position Hardware-Interface")

# ── 5. JointState lesen + Tilt-Befehl senden ─────────────────
section("5. trigger_joint: Position + Reaktionstest")
received = {}


def cb(msg):
    for name, pos in zip(msg.name, msg.position):
        received[name] = pos


node.create_subscription(JointState, "/joint_states", cb, 10)
pub = node.create_publisher(Float64MultiArray, "/tilt_controller/commands", 10)

# 3s sammeln
deadline = time.time() + 3.0
while time.time() < deadline:
    rclpy.spin_once(node, timeout_sec=0.1)

if "trigger_joint" not in received:
    print(f"  {FAIL} trigger_joint nicht in /joint_states")
    print(f"  Empfangene Joints: {sorted(received.keys())}")
else:
    start_pos = received["trigger_joint"]
    start_pos = received["trigger_joint"]
    in_limits = -0.52 <= start_pos <= 0.52
    print(f"  {OK if in_limits else FAIL} "
          f"trigger_joint = {start_pos:.4f} rad  "
          f"({'in Limits [-0.52, 0.52]' if in_limits else 'AUSSERHALB Limits!'})")

    print(f"\n  {INFO} Sende 0.2 rad auf /tilt_controller/commands ...")
    msg_out = Float64MultiArray()
    msg_out.data = [0.2]
    for _ in range(10):
        pub.publish(msg_out)
        rclpy.spin_once(node, timeout_sec=0.1)

    deadline = time.time() + 4.0
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    end_pos = received.get("trigger_joint", start_pos)
    delta = abs(end_pos - start_pos)
    moved = delta > 0.02
    print(f"  Start : {start_pos:.4f} rad")
    print(f"  Jetzt : {end_pos:.4f} rad")
    print(f"  Delta : {delta:.4f} rad")
    print(f"  {OK if moved else FAIL} "
          f"{'Joint bewegt sich!' if moved else 'Joint bewegt sich NICHT'}")

# ── 6. Zusammenfassung ────────────────────────────────────────
section("6. Zusammenfassung")
if "trigger_joint/position" not in all_ifaces:
    print(f"  {FAIL} Hardware-Interface fehlt → ign_ros2_control nicht geladen")
    print("       Pruefe: ros2_control_gazebo_fortress.xacro nutzt "
          "ign_ros2_control/IgnitionSystem?")
elif names_states.get("tilt_controller") != "active":
    state = names_states.get("tilt_controller", "FEHLT")
    print(f"  {FAIL} tilt_controller nicht active (state={state})")
    print("       Pruefe: my_controllers.yaml + PID-Gains vorhanden?")
else:
    print(f"  {OK} Hardware-Interface vorhanden")
    print(f"  {OK} tilt_controller active")
    try:
        sym = OK if moved else FAIL
        print(
            f"  {sym} {'Tilt funktioniert!' if moved else 'Joint reagiert nicht auf Befehl'}")
        if not moved:
            print(
                "       Pruefe: URDF-Limits vs gesendeter Wert (0.2 in [-0.52,0.52]?)")
            print("       Pruefe: PID p-Gain > 0 in my_controllers.yaml?")
    except NameError:
        print(f"  {WARN} JointState nicht lesbar")

node.destroy_node()
rclpy.shutdown()
