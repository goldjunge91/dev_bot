import serial
import time

# Update with your actual device path if different
PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

# Pins from motor_driver.h
LEFT_PWM = 2
LEFT_IN1 = 3
LEFT_IN2 = 4

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # Wait for DTR reset
    print(f"Connected to {PORT}")

    def send(cmd):
        ser.write(f"{cmd}\r".encode())
        print(f"Sent: {cmd}")
        # Response might be "OK" or value
        print(f"Recv: {ser.readline().decode().strip()}")

    print("1. Configuring Pins to OUTPUT...")
    send(f"c {LEFT_PWM} 1")
    send(f"c {LEFT_IN1} 1")
    send(f"c {LEFT_IN2} 1")

    print("\n2. Setting LEFT Motor Direction (IN1=HIGH, IN2=LOW)...")
    send(f"w {LEFT_IN1} 1")
    send(f"w {LEFT_IN2} 0")

    print("\n3. Turning ON PWM Pin (HIGH/Max Speed)...")
    # Using 'w' (digitalWrite) to rule out PWM frequency issues. pure DC.
    send(f"w {LEFT_PWM} 1")

    print("\n--- MOTOR SHOULD SPIN NOW (Wait 3s) ---")
    time.sleep(3)

    print("\n4. Stopping...")
    send(f"w {LEFT_PWM} 0")
    send(f"w {LEFT_IN1} 0")

    ser.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
