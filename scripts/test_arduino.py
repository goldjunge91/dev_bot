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

    # Wichtig: Warte, bis der Arduino UART hochgefahren ist
    time.sleep(2.5)
    ser.reset_input_buffer()

    commands = [
        "ARM",
        "STATUS",
        "TEST_ESC 20",
        "DANGEROUS_SHOT 500",
        "TEST_ESC 0",
        "DISARM",
    ]

    for cmd in commands:
        print(f"> {cmd}")
        # Verwende STRENGSTENS ASCII und strikt nur '\n' als Ende, kein unsichtbares '\r'
        ser.write((cmd + "\n").encode("ascii"))
        time.sleep(2.5)

        while ser.in_waiting > 0:
            resp = ser.readline()
            try:
                print(resp.decode("ascii").strip())
            except UnicodeDecodeError:
                print(f"[RAW]: {resp}")

    ser.close()


if __name__ == "__main__":
    test_pico()
