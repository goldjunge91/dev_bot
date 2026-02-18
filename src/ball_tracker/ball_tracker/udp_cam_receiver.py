import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import socket
import numpy as np


class UdpCamReceiver(Node):
    def __init__(self):
        super().__init__("udp_cam_receiver")

        # Parameter für Port
        self.declare_parameter("port", 9999)
        self.port = self.get_parameter("port").value

        self.publisher_ = self.create_publisher(Image, "/image_raw", 10)
        self.bridge = CvBridge()

        # UDP Socket erstellen
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.port))
        # Non-blocking setzen, damit wir rclpy spin nicht blockieren (oder use threading)
        # Besser: Timer Check
        self.sock.setblocking(False)

        self.timer = self.create_timer(0.01, self.receive_frame)  # Check alle 10ms

        self.get_logger().info(
            f"UDP Receiver gestartet auf Port {self.port}. Warte auf Windows-Stream..."
        )

    def receive_frame(self):
        try:
            # Versuche Daten zu empfangen (Max 65535 Bytes für UDP)
            data, addr = self.sock.recvfrom(65535)

            # Dekodiere JPEG
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Konvertiere zu ROS Nachricht
                msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = "camera_frame"

                self.publisher_.publish(msg)
                self.get_logger().info(f"Frame empfangen von {addr}, PUBLISHED!")

        except BlockingIOError:
            # Keine Daten verfügbar
            pass
        except Exception as e:
            self.get_logger().error(f"Fehler beim Empfang: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = UdpCamReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
