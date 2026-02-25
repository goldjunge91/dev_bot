import serial
import time
import sys


def test_pico():
    try:
        ser = serial.Serial(
            "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00", 115200, timeout=1
        )
        print("Connected to Arduino!")
    except Exception as e:
        print(f"Could not connect: {e}")
        return

    commands = [
        "ARM",
        "STATUS",
        "TEST_ESC 20",
        "DANGEROUS_SHOT 50",
        "TEST_ESC 0",
        "DISARM",
    ]
    for cmd in commands:
        print(f"> {cmd}")
        ser.write((cmd + "\n").encode())
        time.sleep(2.5)  # Wait for arming delay and action
        while ser.in_waiting > 0:
            print(ser.readline().decode().strip())

    ser.close()


if __name__ == "__main__":
    test_pico()
