"""
Motor Debug Script - Direkte Motor-PWM-Steuerung
================================================
Testet Motoren direkt über serielle Verbindung zum Mikrocontroller

Zweck:
- Überprüfung Motor-Verkabelung
- Test Motor-Richtung
- Debugging Pin-Konfiguration
- Kalibrierung

Verwendung:
1. Passe PORT an (siehe unten)
2. Führe Script aus: python3 debug_pins.py
3. Beobachte Motor-Verhalten

Firmware-Befehl:
  'o <left_pwm> <right_pwm>'
  - PWM Bereich: -255 bis +255
  - Negativ = Rückwärts
  - Positiv = Vorwärts
  - 0 = Stopp

Test-Sequenz:
1. Beide Motoren stoppen
2. Linker Motor Rampe (0→200)
3. Rechter Motor Rampe (0→200)
4. Beide Motoren vorwärts
5. Beide Motoren rückwärts
6. Stoppen

WICHTIG:
- Roboter sollte aufgebockt sein (Räder frei)
- Genug Platz um Räder
"""
import serial
import time

# Serielle Port-Konfiguration
# ANPASSEN FÜR DEIN SYSTEM:
# Linux: "/dev/ttyACM0" oder "/dev/serial/by-id/..."
# Windows: "COM3", "COM4", etc.
# macOS: "/dev/cu.usbmodem..."
PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_50443405786ACA1C-if00"
BAUD = 57600  # Baudrate (muss mit Firmware übereinstimmen)

# ============================================================
# Dieses Script verwendet den 'o' Befehl (MOTOR_RAW_PWM):
#
# Funktionen:
# 1. Setzt Auto-Stop-Timer zurück (verhindert Firmware-PWM-Nullung)
# 2. Verwendet firmware's setMotorSpeeds() (korrekte Pin-Behandlung)
# 3. Funktioniert mit allen in motor_driver.h definierten Pins
#
# Befehlsformat:
# 'o <left_pwm> <right_pwm>' - Werte von -255 bis 255
# Negativ = Rückwärts, Positiv = Vorwärts
# ============================================================

try:
    # Serielle Verbindung öffnen
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # Warte auf Verbindungsaufbau
    print(f"Connected to {PORT}")

    def send(cmd):
        """
        Sendet Befehl an Mikrocontroller
        """
        ser.write(f"{cmd}\r".encode())  # \r = Carriage Return (Befehlsende)
        time.sleep(0.05)
        return ser.readline().decode().strip()

    # --- BEIDE MOTOREN STOPPEN ---
    print("Stopping both motors...")
    send("o 0 0")

    # --- LINKER MOTOR RAMPEN-TEST ---
    print("\n=== LEFT MOTOR RAMP TEST ===")
    print("Ramping LEFT motor speed (0 to 200)...")
    for pwm in range(0, 210, 20):  # 0, 20, 40, ..., 200
        print(f"  LEFT PWM: {pwm}/255 (RIGHT: 0)")
        send(f"o {pwm} 0")
        time.sleep(1.0)  # 1 Sekunde pro Schritt

    print("STOPPING...")
    send("o 0 0")
    time.sleep(2)

    # --- RECHTER MOTOR RAMPEN-TEST ---
    print("\n=== RIGHT MOTOR RAMP TEST ===")
    print("Ramping RIGHT motor speed (0 to 200)...")
    for pwm in range(0, 210, 20):
        print(f"  RIGHT PWM: {pwm}/255 (LEFT: 0)")
        send(f"o 0 {pwm}")
        time.sleep(1.0)

    print("STOPPING...")
    send("o 0 0")
    time.sleep(2)

    # --- BEIDE MOTOREN TEST ---
    print("\n=== BOTH MOTORS TEST ===")
    print("Both forward at PWM 150...")
    send("o 150 150")
    time.sleep(3)

    print("Both reverse at PWM 150...")
    send("o -150 -150")  # Negativ = Rückwärts
    time.sleep(3)

    print("STOPPING...")
    send("o 0 0")

    # Verbindung schließen
    ser.close()
    print("\nDone!")

except Exception as e:
    print(f"Error: {e}")
    print("\nMögliche Probleme:")
    print("- Falscher PORT? Prüfe mit 'ls /dev/tty*' (Linux)")
    print("- Mikrocontroller nicht verbunden?")
    print("- Falsche Baudrate? (Standard: 57600)")
