import serial
import time

PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

# Confirmed Left Pins
LEFT_PWM = 5
LEFT_IN1 = 6
LEFT_IN2 = 7

# Candidate Right Pins (Guessing sequential)
RIGHT_CANDIDATE_PWM = 8
RIGHT_CANDIDATE_IN1 = 9
RIGHT_CANDIDATE_IN2 = 10

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"Connected to {PORT}")

    def send(cmd):
        ser.write(f"{cmd}\r".encode())
        # print(f"Sent: {cmd}")
        return ser.readline().decode().strip()

    # --- LEFT MOTOR RAMP TEST ---
    print("\n=== LEFT MOTOR RAMP TEST ===")
    print("Configuring Left Pins...")
    send(f"c {LEFT_PWM} 1")
    send(f"c {LEFT_IN1} 1")
    send(f"c {LEFT_IN2} 1")

    print("Setting Direction...")
    send(f"w {LEFT_IN1} 1")
    send(f"w {LEFT_IN2} 0")

    print("Ramping PWM from 0 to 255...")
    for pwm in range(0, 256, 10):
        print(f"PWM: {pwm}")
        send(f"x {LEFT_PWM} {pwm}")
        time.sleep(0.2)

    print("STOPPING Left...")
    send(f"w {LEFT_PWM} 0")
    send(f"w {LEFT_IN1} 0")
    pass

    time.sleep(2)

    # --- RIGHT MOTOR DISCOVERY ---
    print("\n=== RIGHT MOTOR TEST (Pins 8, 9, 10) ===")
    print("If this works, we found the Right Motor.")

    print("Configuring Right Candidate Pins...")
    send(f"c {RIGHT_CANDIDATE_PWM} 1")
    send(f"c {RIGHT_CANDIDATE_IN1} 1")
    send(f"c {RIGHT_CANDIDATE_IN2} 1")

    print("Setting Right Direction...")
    send(f"w {RIGHT_CANDIDATE_IN1} 1")
    send(f"w {RIGHT_CANDIDATE_IN2} 0")

    print("Full Power Right...")
    send(f"w {RIGHT_CANDIDATE_PWM} 1")

    time.sleep(3)

    print("STOPPING Right...")
    send(f"w {RIGHT_CANDIDATE_PWM} 0")
    send(f"w {RIGHT_CANDIDATE_IN1} 0")

    ser.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
