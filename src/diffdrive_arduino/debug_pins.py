import serial
import time

# Update with your actual device path if different
PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

# Pins from motor_driver.h (Left Side Only)
LEFT_PWM = 5
LEFT_IN1 = 6
LEFT_IN2 = 7

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # Wait for DTR reset
    print(f"Connected to {PORT}")

    def send(cmd):
        ser.write(f"{cmd}\r".encode())
        print(f"Sent: {cmd}")
        print(f"Recv: {ser.readline().decode().strip()}")

    print("--- LEFT MOTOR TEST ---")

    print("1. Configuring Pins to OUTPUT...")
    send(f"c {LEFT_PWM} 1")
    send(f"c {LEFT_IN1} 1")
    send(f"c {LEFT_IN2} 1")

    print("\n2. Setting Direction (IN1=High, IN2=Low)...")
    send(f"w {LEFT_IN1} 1")
    send(f"w {LEFT_IN2} 0")

    print("\n3. Digital Write High (Max Speed)...")
    print(">>> MOTOR SHOULD BE SPINNING FAST NOW <<<")
    send(f"w {LEFT_PWM} 1")
    time.sleep(5)

    print(">>> STOPPING (Hard Brake) <<<")
    send(f"w {LEFT_PWM} 0")
    send(f"w {LEFT_IN1} 0")
    send(f"w {LEFT_IN2} 0")

    print("\n[STOPPED] Preparing for PWM Test in:")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print(">>> GO! <<<")

    print("\nNeed to reset direction for PWM Test...")
    send(f"w {LEFT_IN1} 1")
    send(f"w {LEFT_IN2} 0")

    print("\n4. PWM Test (Analog Write 100/255)...")
    print(">>> MOTOR SHOULD BE SPINNING SLOWER (~40%) NOW <<<")
    # Using 'x' command for analogWrite
    send(f"x {LEFT_PWM} 100")
    time.sleep(5)

    print(">>> STOPPING (Hard Brake) <<<")
    send(f"w {LEFT_PWM} 0")
    send(f"w {LEFT_IN1} 0")
    send(f"w {LEFT_IN2} 0")

    ser.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
