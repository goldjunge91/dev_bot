import serial
import time


def test_motors():
    port = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
    baud = 57600

    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Wait for connection

        print(f"Connected to {port} at {baud}")

        # Reset encoders
        print("Resetting encoders...")
        ser.write(b"r\r")
        time.sleep(0.1)
        response = ser.readline().decode().strip()
        print(f"Response: {response}")

        # Move forward
        print("Moving forward (speed 50)...")
        ser.write(b"o 50 50\r")

        start_time = time.time()
        while time.time() - start_time < 2:
            # Read encoders while moving
            ser.write(b"e\r")
            line = ser.readline().decode().strip()
            if line:
                print(f"Encoders: {line}")
            time.sleep(0.1)

        # Stop
        print("Stopping...")
        ser.write(b"o 0 0\r")
        time.sleep(0.1)
        response = ser.readline().decode().strip()
        print(f"Stop response: {response}")

        ser.close()
        print("Test complete.")

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    test_motors()
