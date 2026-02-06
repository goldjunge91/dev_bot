import serial
import time

# Update with your actual device path if different
PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

# Pins from motor_driver.h
# Left
LEFT_PWM = 2
LEFT_IN1 = 3
LEFT_IN2 = 4
# Right
RIGHT_PWM = 6
RIGHT_IN1 = 7
RIGHT_IN2 = 8

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # Wait for DTR reset
    print(f"Connected to {PORT}")

    def send(cmd):
        ser.write(f"{cmd}\r".encode())
        print(f"Sent: {cmd}")
        print(f"Recv: {ser.readline().decode().strip()}")

    print("--- TEST 1: RIGHT Motor Digital Check ---")
    print("Configuring RIGHT Pins to OUTPUT...")
    send(f"c {RIGHT_PWM} 1")
    send(f"c {RIGHT_IN1} 1")
    send(f"c {RIGHT_IN2} 1")

    print("Setting RIGHT Motor Direction...")
    send(f"w {RIGHT_IN1} 1")
    send(f"w {RIGHT_IN2} 0")

    print("Turning ON RIGHT PWM Pin (HIGH - Full Speed)...")
    send(f"w {RIGHT_PWM} 1")

    time.sleep(2)
    print("Stop RIGHT...")
    send(f"w {RIGHT_PWM} 0")

    print("\n--- TEST 2: PWM Check (Left Motor) ---")
    # Does analogWrite work?
    print("Setting LEFT Motor Direction...")
    # Re-config in case reset
    send(f"c {LEFT_PWM} 1")
    send(f"c {LEFT_IN1} 1")
    send(f"c {LEFT_IN2} 1")
    send(f"w {LEFT_IN1} 1")
    send(f"w {LEFT_IN2} 0")

    print("Sending analogWrite (PWM) 200/255 to LEFT...")
    # 'x' is ANALOG_WRITE in commands.h
    send(f"x {LEFT_PWM} 200")

    time.sleep(2)
    print("Stop PWM...")
    send(f"w {LEFT_PWM} 0")

    print("\n--- TEST 3: PWM Check (Right Motor) ---")
    # Does analogWrite work?
    print("Setting Right Motor Direction...")
    # Re-config in case reset
    send(f"c {RIGHT_PWM} 1")
    send(f"c {RIGHT_IN1} 1")
    send(f"c {RIGHT_IN2} 1")
    send(f"w {RIGHT_IN1} 1")
    send(f"w {RIGHT_IN2} 0")

    print("Sending analogWrite (PWM) 200/255 to RIGHT...")
    # 'x' is ANALOG_WRITE in commands.h
    send(f"x {RIGHT_PWM} 200")

    time.sleep(2)
    print("Stop PWM...")
    send(f"w {RIGHT_PWM} 0")

    ser.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
