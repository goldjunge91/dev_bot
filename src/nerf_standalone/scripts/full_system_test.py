#!/usr/bin/env python3
"""
Full System Test - Kompletter Roboter + Nerf Launcher Test
===========================================================
Testet alle Hauptkomponenten des Systems:
Tests all main components of the system:

1. Basis-Test / Base Test:
   - Differential Drive Bewegung / Differential drive movement
   - Encoder Feedback / Encoder feedback
   
2. Nerf-Test / Nerf Test:
   - Arming System
   - Tilt Servo (verschiedene Positionen / different positions)
   - Fire Service (komplette Schuss-Sequenz / complete fire sequence)

Verwendung / Usage:
  ros2 run nerf_standalone full_system_test.py

WICHTIG / IMPORTANT:
- Stelle sicher dass Hardware verbunden ist / Ensure hardware is connected
- Genug Platz für Roboter-Bewegung / Enough space for robot movement
- Sicherheitsabstand beim Schießen / Safety distance when firing
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
import time
import math


class FullSystemTest(Node):
    def __init__(self):
        super().__init__("full_system_test")

        # Publishers: Steuern Roboter und Launcher / Control robot and launcher
        self.cmd_vel_pub = self.create_publisher(
            Twist, "/diff_cont/cmd_vel_unstamped", 10  # Queue Size: 10 Nachrichten puffern / Buffer 10 messages
        )
        self.trigger_pub = self.create_publisher(
            Float64MultiArray, "/trigger_controller/commands", 10  # Tilt Servo
        )
        self.arming_pub = self.create_publisher(
            Float64MultiArray, "/arming_controller/commands", 10  # Arming System
        )

        # Subscribers: Empfängt Encoder-Feedback / Receives encoder feedback
        self.create_subscription(JointState, "/joint_states", self.joint_callback, 10)

        # Service Clients: Ruft Fire-Service auf / Calls fire service
        self.fire_client = self.create_client(Trigger, "/nerf/fire")

        # Zustandsvariablen / State variables
        self.wheel_vels = {}  # Speichert Rad-Geschwindigkeiten / Stores wheel velocities
        self.get_logger().info("Full System Test Node Started")

    def joint_callback(self, msg):
        """
        Speichert Rad-Geschwindigkeiten für Feedback
        Stores wheel velocities for feedback
        """
        for name, vel in zip(msg.name, msg.velocity):
            self.wheel_vels[name] = vel

    def run_base_test(self):
        """
        Testet Differential Drive Basis
        Tests differential drive base
        
        Test-Ablauf / Test sequence:
        1. Vorwärts fahren 2s bei 0.2 m/s / Move forward 2s at 0.2 m/s
        2. Encoder-Feedback prüfen / Check encoder feedback
        3. Stoppen / Stop
        """
        self.get_logger().info("--- STARTING BASE TEST ---")

        # Vorwärts fahren / Move forward
        msg = Twist()
        msg.linear.x = 0.2  # 0.2 m/s vorwärts / forward
        self.get_logger().info("Moving Forward at 0.2 m/s...")
        end_time = time.time() + 2.0
        while time.time() < end_time:
            self.cmd_vel_pub.publish(msg)
            # Prüfe Feedback / Check feedback
            left_vel = self.wheel_vels.get("left_wheel_joint", 0.0)
            right_vel = self.wheel_vels.get("right_wheel_joint", 0.0)
            self.get_logger().info(
                f"Encoders: L={left_vel:.2f}, R={right_vel:.2f}",
                throttle_duration_sec=0.5,  # Nur alle 0.5s loggen / Log only every 0.5s
            )
            time.sleep(0.1)

        # Stoppen / Stop
        msg.linear.x = 0.0
        self.cmd_vel_pub.publish(msg)
        self.get_logger().info("Stopping Base.")
        time.sleep(1.0)

    def run_nerf_test(self):
        """
        Testet Nerf Launcher Funktionalität
        Tests Nerf launcher functionality
        
        Test-Ablauf / Test sequence:
        1. System armen (WICHTIG für NerfSystem Hardware!)
           Arm system (IMPORTANT for NerfSystem hardware!)
        2. Tilt-Positionen testen (Unten, Oben, Mitte)
           Test tilt positions (Down, Up, Middle)
        3. Fire-Service aufrufen (komplette Schuss-Sequenz)
           Call fire service (complete fire sequence)
        4. System disarmen
           Disarm system
        """
        self.get_logger().info("--- STARTING NERF TEST ---")

        # 1. SYSTEM ARMEN (Erforderlich für NerfSystem Hardware)
        # 1. ARM THE SYSTEM (Required for NerfSystem hardware)
        self.get_logger().info("Arming System... (Waiting 2s)")
        arm_cmd = Float64MultiArray()
        arm_cmd.data = [1.0]  # 1.0 = Armed
        # Mehrfach publizieren um sicherzustellen dass es empfangen wird
        # Publish multiple times to ensure it's received
        for _ in range(5):
            self.arming_pub.publish(arm_cmd)
            time.sleep(0.1)
        time.sleep(1.5)  # Warte auf Arming-Sequenz/Sicherheit / Wait for arming sequence/safety

        # Tilt-Positionen testen / Test tilt positions
        targets = [5.23, 6.28, 5.75]  # Unten/Down, Oben/Up, Mitte/Middle
        for t in targets:
            self.get_logger().info(f"Tilting to {t:.2f} rad")
            cmd = Float64MultiArray()
            cmd.data = [t]
            self.trigger_pub.publish(cmd)
            time.sleep(2.0)  # Warte auf Servo-Bewegung / Wait for servo movement

        # Fire-Service testen / Test fire service
        self.get_logger().info("Testing Fire Sequence...")
        if self.fire_client.wait_for_service(timeout_sec=2.0):
            req = Trigger.Request()
            future = self.fire_client.call_async(req)
            rclpy.spin_until_future_complete(self, future)
            self.get_logger().info(f"Fire Result: {future.result().message}")
        else:
            self.get_logger().error("Fire Service not available!")

        # DISARM am Ende / DISARM at the end
        self.get_logger().info("Disarming System...")
        arm_cmd.data = [0.0]  # 0.0 = Disarmed
        self.arming_pub.publish(arm_cmd)
        time.sleep(0.5)


def main():
    rclpy.init()
    node = FullSystemTest()

    try:
        # Run tests in separate thread or simple block since we are script
        node.run_base_test()
        node.run_nerf_test()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
