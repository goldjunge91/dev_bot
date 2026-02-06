import serial
import time

# Update with your actual device path if different
PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"Connected to {PORT}")

    # 1. Raw PWM Forward (Avoids PID)
    # Using 255 (Max) to ensure it's not a stall issue.
    # If this fails, analogWrite() on the Pico might be broken/unsupported.
    print("Sending RAW PWM: o 255 255")
    ser.write(b"o 255 255\r")
    response = ser.readline().decode().strip()
    print(f"Response: {response}")

    time.sleep(2)

    # 2. Stop
    print("Stopping")
    ser.write(b"o 0 0\r")

    # 3. Read Encoders
    ser.write(b"e\r")
    print(f"Encoders: {ser.readline().decode().strip()}")

    ser.close()
except Exception as e:
    print(f"Error: {e}")
