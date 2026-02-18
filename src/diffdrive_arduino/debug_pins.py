"""
Motor Debug Script - Direkte Motor-PWM-Steuerung
================================================
Testet Motoren direkt über serielle Verbindung zum Mikrocontroller
Tests motors directly via serial connection to microcontroller

Zweck / Purpose:
- Überprüfung Motor-Verkabelung / Check motor wiring
- Test Motor-Richtung / Test motor direction
- Debugging Pin-Konfiguration / Debug pin configuration
- Kalibrierung / Calibration

Verwendung / Usage:
1. Passe PORT an (siehe unten) / Adjust PORT (see below)
2. Führe Script aus: python3 debug_pins.py / Run script: python3 debug_pins.py
3. Beobachte Motor-Verhalten / Observe motor behavior

Firmware-Befehl / Firmware Command:
  'o <left_pwm> <right_pwm>'
  - PWM Bereich: -255 bis +255 / PWM range: -255 to +255
  - Negativ = Rückwärts / Negative = reverse
  - Positiv = Vorwärts / Positive = forward
  - 0 = Stopp / 0 = stop

Test-Sequenz / Test Sequence:
1. Beide Motoren stoppen / Stop both motors
2. Linker Motor Rampe (0→200) / Left motor ramp (0→200)
3. Rechter Motor Rampe (0→200) / Right motor ramp (0→200)
4. Beide Motoren vorwärts / Both motors forward
5. Beide Motoren rückwärts / Both motors reverse
6. Stoppen / Stop

WICHTIG / IMPORTANT:
- Roboter sollte aufgebockt sein (Räder frei)
  Robot should be elevated (wheels free)
- Genug Platz um Räder / Enough space around wheels
"""
import serial
import time

# Serielle Port-Konfiguration / Serial port configuration
# ANPASSEN FÜR DEIN SYSTEM / ADJUST FOR YOUR SYSTEM:
# Linux: "/dev/ttyACM0" oder "/dev/serial/by-id/..."
# Windows: "COM3", "COM4", etc.
# macOS: "/dev/cu.usbmodem..."
PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_50443405786ACA1C-if00"
BAUD = 57600  # Baudrate (muss mit Firmware übereinstimmen / must match firmware)

# ============================================================
# Dieses Script verwendet den 'o' Befehl (MOTOR_RAW_PWM):
# This script uses the 'o' command (MOTOR_RAW_PWM):
#
# Funktionen / Functions:
# 1. Setzt Auto-Stop-Timer zurück (verhindert Firmware-PWM-Nullung)
#    Resets auto-stop timer (prevents firmware from zeroing PWM)
# 2. Verwendet firmware's setMotorSpeeds() (korrekte Pin-Behandlung)
#    Uses firmware's setMotorSpeeds() (correct pin handling)
# 3. Funktioniert mit allen in motor_driver.h definierten Pins
#    Works with whatever pins are defined in motor_driver.h
#
# Befehlsformat / Command format:
# 'o <left_pwm> <right_pwm>' - Werte von -255 bis 255
# 'o <left_pwm> <right_pwm>' - values from -255 to 255
# Negativ = Rückwärts, Positiv = Vorwärts
# Negative = reverse, Positive = forward
# ============================================================

try:
    # Serielle Verbindung öffnen / Open serial connection
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # Warte auf Verbindungsaufbau / Wait for connection
    print(f"Connected to {PORT}")

    def send(cmd):
        """
        Sendet Befehl an Mikrocontroller
        Sends command to microcontroller
        """
        ser.write(f"{cmd}\r".encode())  # \r = Carriage Return (Befehlsende)
        time.sleep(0.05)
        return ser.readline().decode().strip()

    # --- BEIDE MOTOREN STOPPEN / STOP BOTH MOTORS ---
    print("Stopping both motors...")
    send("o 0 0")

    # --- LINKER MOTOR RAMPEN-TEST / LEFT MOTOR RAMP TEST ---
    print("\n=== LEFT MOTOR RAMP TEST ===")
    print("Ramping LEFT motor speed (0 to 200)...")
    for pwm in range(0, 210, 20):  # 0, 20, 40, ..., 200
        print(f"  LEFT PWM: {pwm}/255 (RIGHT: 0)")
        send(f"o {pwm} 0")
        time.sleep(1.0)  # 1 Sekunde pro Schritt / 1 second per step

    print("STOPPING...")
    send("o 0 0")
    time.sleep(2)

    # --- RECHTER MOTOR RAMPEN-TEST / RIGHT MOTOR RAMP TEST ---
    print("\n=== RIGHT MOTOR RAMP TEST ===")
    print("Ramping RIGHT motor speed (0 to 200)...")
    for pwm in range(0, 210, 20):
        print(f"  RIGHT PWM: {pwm}/255 (LEFT: 0)")
        send(f"o 0 {pwm}")
        time.sleep(1.0)

    print("STOPPING...")
    send("o 0 0")
    time.sleep(2)

    # --- BEIDE MOTOREN TEST / BOTH MOTORS TEST ---
    print("\n=== BOTH MOTORS TEST ===")
    print("Both forward at PWM 150...")
    send("o 150 150")
    time.sleep(3)

    print("Both reverse at PWM 150...")
    send("o -150 -150")  # Negativ = Rückwärts / Negative = reverse
    time.sleep(3)

    print("STOPPING...")
    send("o 0 0")

    # Verbindung schließen / Close connection
    ser.close()
    print("\nDone!")

except Exception as e:
    print(f"Error: {e}")
    print("\nMögliche Probleme / Possible issues:")
    print("- Falscher PORT? Prüfe mit 'ls /dev/tty*' (Linux)")
    print("  Wrong PORT? Check with 'ls /dev/tty*' (Linux)")
    print("- Mikrocontroller nicht verbunden?")
    print("  Microcontroller not connected?")
    print("- Falsche Baudrate? (Standard: 57600)")
    print("  Wrong baud rate? (Default: 57600)")
