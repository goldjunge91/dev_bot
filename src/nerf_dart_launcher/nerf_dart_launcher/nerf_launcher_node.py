"""Nerf Launcher Node with Serial Bridge.

This node provides ROS 2 topics to control a Nerf launcher via serial
communication with an Arduino Pro Micro.

Topics (subscribers):
- ~/cmd/arm (std_msgs/Bool): True=ARM, False=DISARM
- ~/cmd/fire (std_msgs/Bool): True=execute SHOT sequence
- ~/cmd/tilt (std_msgs/Float32): Tilt angle in degrees (0-180)
- ~/cmd/power (std_msgs/Float32): ESC power for next shot (0-80%)

Topics (publishers):
- ~/status/armed (std_msgs/Bool): Current armed state
- ~/status/connected (std_msgs/Bool): Serial connection status

Parameters:
- serial_port (str): Serial port path (default: /dev/ttyACM0)
- baud_rate (int): Baud rate (default: 115200)
- reconnect_interval (float): Seconds between reconnect attempts (default: 2.0)

Author: goldjunge91
"""

from __future__ import annotations

import threading
from typing import Optional

import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool, Float32

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class NerfLauncherNode(Node):
    """ROS 2 node bridging topics to Arduino Nerf Launcher via serial."""

    def __init__(self) -> None:
        super().__init__("nerf_launcher")

        # Parameters
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("reconnect_interval", 2.0)

        self._port = self.get_parameter("serial_port").value
        self._baud = self.get_parameter("baud_rate").value
        self._reconnect_interval = self.get_parameter("reconnect_interval").value

        # State
        self._serial: Optional[serial.Serial] = None
        self._serial_lock = threading.Lock()
        self._is_armed = False
        self._shot_power = 40  # Default power

        # Check pyserial
        if not SERIAL_AVAILABLE:
            self.get_logger().error("pyserial not installed! Run: pip install pyserial")
            return

        # Publishers (status)
        self._armed_pub = self.create_publisher(Bool, "status/armed", 10)
        self._connected_pub = self.create_publisher(Bool, "status/connected", 10)

        # Subscribers (commands) 
        self.create_subscription(Bool, "cmd/arm", self._on_arm, 10)
        self.create_subscription(Bool, "cmd/fire", self._on_fire, 10)
        self.create_subscription(Float32, "cmd/tilt", self._on_tilt, 10)
        self.create_subscription(Float32, "cmd/power", self._on_power, 10)

        # Serial reader thread
        self._running = True
        self._reader_thread = threading.Thread(target=self._serial_reader, daemon=True)
        self._reader_thread.start()

        # Status timer
        self.create_timer(1.0, self._publish_status)

        # Initial connection
        self._connect_serial()

        self.get_logger().info(
            f"Nerf Launcher Node started. Port: {self._port}, Baud: {self._baud}"
        )

    def _connect_serial(self) -> bool:
        """Try to connect to the Arduino."""
        if self._serial and self._serial.is_open:
            return True

        try:
            self._serial = serial.Serial(
                self._port, 
                self._baud, 
                timeout=0.1
            )
            self.get_logger().info(f"Connected to {self._port}")
            return True
        except serial.SerialException as e:
            self.get_logger().warn(f"Serial connection failed: {e}")
            self._serial = None
            return False

    def _send_command(self, cmd: str) -> bool:
        """Send a command to the Arduino."""
        with self._serial_lock:
            if not self._serial or not self._serial.is_open:
                if not self._connect_serial():
                    self.get_logger().error("Cannot send command - not connected")
                    return False
            try:
                self._serial.write(f"{cmd}\n".encode())
                self._serial.flush()
                self.get_logger().debug(f"Sent: {cmd}")
                return True
            except serial.SerialException as e:
                self.get_logger().error(f"Serial write failed: {e}")
                self._serial = None
                return False

    def _serial_reader(self) -> None:
        """Background thread reading serial responses."""
        while self._running:
            with self._serial_lock:
                ser = self._serial
            
            if not ser or not ser.is_open:
                # Try to reconnect
                import time
                time.sleep(self._reconnect_interval)
                self._connect_serial()
                continue

            try:
                if ser.in_waiting:
                    line = ser.readline().decode().strip()
                    if line:
                        self._handle_response(line)
            except serial.SerialException:
                with self._serial_lock:
                    self._serial = None
            except Exception as e:
                self.get_logger().debug(f"Serial read error: {e}")

    def _handle_response(self, line: str) -> None:
        """Handle response from Arduino."""
        self.get_logger().info(f"Arduino: {line}")
        
        # Parse status updates
        if "ARMED" in line and "DISARMED" not in line:
            self._is_armed = True
        elif "DISARMED" in line:
            self._is_armed = False

    def _publish_status(self) -> None:
        """Publish current status."""
        connected = self._serial is not None and self._serial.is_open
        self._connected_pub.publish(Bool(data=connected))
        self._armed_pub.publish(Bool(data=self._is_armed))

    # === Topic Callbacks ===

    def _on_arm(self, msg: Bool) -> None:
        """Handle ARM/DISARM command."""
        if msg.data:
            self._send_command("ARM")
        else:
            self._send_command("DISARM")

    def _on_fire(self, msg: Bool) -> None:
        """Handle FIRE command."""
        if msg.data:
            self._send_command(f"SHOT {self._shot_power}")

    def _on_tilt(self, msg: Float32) -> None:
        """Handle TILT command."""
        angle = int(max(0, min(180, msg.data)))
        self._send_command(f"TILT {angle}")

    def _on_power(self, msg: Float32) -> None:
        """Set power for next shot (0-80%)."""
        self._shot_power = int(max(0, min(80, msg.data)))
        self.get_logger().info(f"Shot power set to {self._shot_power}%")

    def destroy_node(self) -> None:
        """Clean shutdown."""
        self._running = False
        if self._serial and self._serial.is_open:
            self._send_command("DISARM")
            self._serial.close()
        super().destroy_node()


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node = NerfLauncherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
