import serial
import time

PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

# Confirmed Left Pins
LEFT_PWM = 0
LEFT_IN1 = 4
LEFT_IN2 = 5

# Candidate Right Pins (Guessing sequential)
RIGHT_PWM = 6
RIGHT_IN1 = 7
RIGHT_IN2 = 8

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"Connected to {PORT}")

    def send(cmd):
        ser.write(f"{cmd}\r".encode())
        # print(f"Sent: {cmd}")
        return ser.readline().decode().strip()

    # Disable all
    send(f"w {LEFT_PWM} 0")
    send(f"w {LEFT_IN1} 0")
    send(f"w {RIGHT_PWM} 0")
    send(f"w {RIGHT_IN1} 0")

    # --- LEFT MOTOR RAMP TEST ---
    print("\n=== LEFT MOTOR RAMP TEST ===")
    print("Configuring Left Pins...")
    send(f"c {LEFT_PWM} 1")
    send(f"c {LEFT_IN1} 1")
    send(f"c {LEFT_IN2} 1")

    print("Setting Direction...")
    send(f"w {LEFT_IN1} 1")
    send(f"w {LEFT_IN2} 0")

    print("\n--- LOW SPEED RAMP (0 to 100) ---")
    print("Checking for ANY speed change...")
    for pwm in range(0, 105, 10):
        print(f"PWM: {pwm}/255")
        send(f"x {LEFT_PWM} {pwm}")
        time.sleep(1.0)  # Longer wait to observe

    print("STOPPING Left...")
    send(f"w {LEFT_PWM} 0")
    send(f"w {LEFT_IN1} 0")
    pass

    time.sleep(2)

    # --- RIGHT MOTOR DISCOVERY ---
    print("\n=== RIGHT MOTOR TEST (Pins6, 7, 8) ===")
    print("If this works, we found the Right Motor.")

    print("Configuring Right Candidate Pins...")
    send(f"c {RIGHT_PWM} 1")
    send(f"c {RIGHT_IN1} 1")
    send(f"c {RIGHT_IN2} 1")

    print("Setting Right Direction...")
    send(f"w {RIGHT_IN1} 1")
    send(f"w {RIGHT_IN2} 0")
    print("\n--- LOW SPEED RAMP (0 to 100) ---")
    print("Checking for ANY speed change...")
    for pwm in range(0, 105, 10):
        print(f"PWM: {pwm}/255")
        send(f"x {RIGHT_PWM} {pwm}")
        time.sleep(1.0)  # Longer wait to observe

    # print("Full Power Right...")
    # send(f"w {RIGHT_PWM} 1")

    time.sleep(3)

    print("STOPPING Right...")
    send(f"w {RIGHT_PWM} 0")
    send(f"w {RIGHT_IN1} 0")

    ser.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
