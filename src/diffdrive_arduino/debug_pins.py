import serial
import time

PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_50443405786ACA1C-if00"
BAUD = 57600

# ============================================================
# This script uses the 'o' command (MOTOR_RAW_PWM) which:
# 1. Resets the auto-stop timer (prevents firmware from zeroing PWM)
# 2. Uses the firmware's setMotorSpeeds() (correct pin handling)
# 3. Works with whatever pins are defined in motor_driver.h
#
# 'o <left_pwm> <right_pwm>' - values from -255 to 255
# Negative = reverse, Positive = forward
# ============================================================

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print(f"Connected to {PORT}")

    def send(cmd):
        ser.write(f"{cmd}\r".encode())
        time.sleep(0.05)
        return ser.readline().decode().strip()

    # --- STOP BOTH ---
    print("Stopping both motors...")
    send("o 0 0")

    # --- LEFT MOTOR RAMP TEST ---
    print("\n=== LEFT MOTOR RAMP TEST ===")
    print("Ramping LEFT motor speed (0 to 200)...")
    for pwm in range(0, 210, 20):
        print(f"  LEFT PWM: {pwm}/255 (RIGHT: 0)")
        send(f"o {pwm} 0")
        time.sleep(1.0)

    print("STOPPING...")
    send("o 0 0")
    time.sleep(2)

    # --- RIGHT MOTOR RAMP TEST ---
    print("\n=== RIGHT MOTOR RAMP TEST ===")
    print("Ramping RIGHT motor speed (0 to 200)...")
    for pwm in range(0, 210, 20):
        print(f"  RIGHT PWM: {pwm}/255 (LEFT: 0)")
        send(f"o 0 {pwm}")
        time.sleep(1.0)

    print("STOPPING...")
    send("o 0 0")
    time.sleep(2)

    # --- BOTH MOTORS ---
    print("\n=== BOTH MOTORS TEST ===")
    print("Both forward at PWM 150...")
    send("o 150 150")
    time.sleep(3)

    print("Both reverse at PWM 150...")
    send("o -150 -150")
    time.sleep(3)

    print("STOPPING...")
    send("o 0 0")

    ser.close()
    print("\nDone!")

except Exception as e:
    print(f"Error: {e}")
