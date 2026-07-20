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
IMU-Hardware-Test für den echten Roboter.

=========================================
Prüft die live IMU-Daten (/imu/data vom imu_broadcaster), während der
Roboter STILL STEHT. Nicht bewegen während des Tests!

Checks:
  1. Rate        — Nachrichten kommen an (Soll ~100 Hz, controller_manager)
  2. frame_id    — muss 'imu_link' sein
  3. Quaternion  — Orientierung ist normiert (|q| ≈ 1)
  4. Gyro-Ruhe   — Winkelgeschwindigkeit ≈ 0 im Stand (Bias-Check)
  5. Gravitation — |Beschleunigung| ≈ 9.81 m/s² (Accel liefert plausibel)
  6. Yaw-Drift   — Orientierungsdrift im Stand (Komplementärfilter)
  7. Timestamps  — monoton steigend, nicht 0

Voraussetzung: Basis-Bringup läuft (launch_all_real.launch.py).
Läuft auf dem Pi ODER auf dem PC (gleiche DDS-Config).

Verwendung:
  ros2 run gubot_utils imu_hw_test.py
  ros2 run gubot_utils imu_hw_test.py --duration 20 --min-rate 80
Exit-Code 0 = alle Checks bestanden, 1 = mindestens ein FAIL.
"""

import argparse
import math
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu

GYRO_REST_MAX = 0.05  # rad/s — mehr im Stand = Bewegung oder Bias
QUAT_NORM_TOL = 0.02  # |q| darf so weit von 1 abweichen
GRAVITY_RANGE = (8.0, 11.6)  # m/s² — plausibles |accel| mit Gravitation
YAW_DRIFT_WARN = 0.2  # deg/s
YAW_DRIFT_FAIL = 2.0  # deg/s


def yaw_from_quat(x, y, z, w):
    """Yaw (rad) aus Quaternion (ZYX-Konvention)."""
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


class ImuCollector(Node):
    """Sammelt IMU-Messages für die Testdauer."""

    def __init__(self, topic):
        super().__init__("imu_hw_test")
        self.msgs = []
        self.sub = self.create_subscription(Imu, topic, self.msgs.append, qos_profile_sensor_data)


def run_checks(msgs, duration, min_rate):
    """Führt alle Checks aus; gibt Anzahl der FAILs zurück."""
    results = []  # (status, name, detail)

    def check(ok, name, detail, warn=False):
        status = "PASS" if ok else ("WARN" if warn else "FAIL")
        results.append((status, name, detail))

    # 1. Rate
    rate = len(msgs) / duration
    check(rate >= min_rate, "Rate", f"{rate:.1f} Hz (min {min_rate:.0f}, Soll ~100)")

    if len(msgs) >= 10:
        # 2. frame_id
        frames = {m.header.frame_id for m in msgs}
        check(frames == {"imu_link"}, "frame_id", f"{sorted(frames)}")

        # 3. Quaternion normiert
        norms = [
            math.sqrt(
                m.orientation.x**2 + m.orientation.y**2 + m.orientation.z**2 + m.orientation.w**2
            )
            for m in msgs
        ]
        worst = max(abs(n - 1.0) for n in norms)
        check(
            worst < QUAT_NORM_TOL,
            "Quaternion-Norm",
            f"max |1-|q|| = {worst:.4f} (Toleranz {QUAT_NORM_TOL})",
        )

        # 4. Gyro in Ruhe
        for axis in ("x", "y", "z"):
            mean = sum(getattr(m.angular_velocity, axis) for m in msgs) / len(msgs)
            check(
                abs(mean) < GYRO_REST_MAX,
                f"Gyro-Ruhe {axis}",
                f"Mittel {mean:+.4f} rad/s (max ±{GYRO_REST_MAX})",
            )

        # 5. Gravitation
        acc = [
            math.sqrt(
                m.linear_acceleration.x**2
                + m.linear_acceleration.y**2
                + m.linear_acceleration.z**2
            )
            for m in msgs
        ]
        mean_acc = sum(acc) / len(acc)
        lo, hi = GRAVITY_RANGE
        check(
            lo <= mean_acc <= hi,
            "Gravitation",
            f"|accel| Mittel = {mean_acc:.2f} m/s² (erwartet {lo}–{hi})",
            warn=True,
        )

        # 6. Yaw-Drift im Stand
        o0, o1 = msgs[0].orientation, msgs[-1].orientation
        yaw0 = yaw_from_quat(o0.x, o0.y, o0.z, o0.w)
        yaw1 = yaw_from_quat(o1.x, o1.y, o1.z, o1.w)
        diff = math.degrees(math.atan2(math.sin(yaw1 - yaw0), math.cos(yaw1 - yaw0)))
        drift = abs(diff) / duration
        if drift >= YAW_DRIFT_FAIL:
            check(False, "Yaw-Drift", f"{drift:.3f} deg/s — viel zu hoch")
        else:
            check(
                drift < YAW_DRIFT_WARN,
                "Yaw-Drift",
                f"{drift:.3f} deg/s (warn ab {YAW_DRIFT_WARN})",
                warn=True,
            )

        # 7. Timestamps monoton & nicht 0
        stamps = [m.header.stamp.sec + m.header.stamp.nanosec * 1e-9 for m in msgs]
        monotonic = all(b >= a for a, b in zip(stamps, stamps[1:]))
        check(
            monotonic and stamps[0] > 0,
            "Timestamps",
            "monoton steigend, > 0" if monotonic else "NICHT monoton / null",
        )

    print("\n" + "=" * 62)
    print("IMU-HARDWARE-TEST — Ergebnis")
    print("=" * 62)
    fails = 0
    for status, name, detail in results:
        mark = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[status]
        print(f"  {mark} [{status}] {name:<18} {detail}")
        if status == "FAIL":
            fails += 1
    print("=" * 62)
    print("ALLE CHECKS BESTANDEN" if fails == 0 else f"{fails} CHECK(S) FEHLGESCHLAGEN")
    return fails


def main():
    parser = argparse.ArgumentParser(
        description="IMU-Hardware-Test (Roboter still stehen lassen!)"
    )
    parser.add_argument("--topic", default="/imu/data")
    parser.add_argument(
        "--duration", type=float, default=10.0, help="Messdauer in Sekunden (Standard 10)"
    )
    parser.add_argument(
        "--min-rate", type=float, default=50.0, help="Mindest-Publikationsrate in Hz (Standard 50)"
    )
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = ImuCollector(args.topic)
    print(f"Sammle {args.duration:.0f}s IMU-Daten von {args.topic} — " f"Roboter NICHT bewegen...")

    end = node.get_clock().now().nanoseconds + int(args.duration * 1e9)
    while rclpy.ok() and node.get_clock().now().nanoseconds < end:
        rclpy.spin_once(node, timeout_sec=0.1)

    if not node.msgs:
        print(
            f"\nFAIL: Keine Nachrichten auf {args.topic}. "
            "Läuft launch_all_real.launch.py? DDS-Config identisch?"
        )
        fails = 1
    else:
        fails = run_checks(node.msgs, args.duration, args.min_rate)

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
