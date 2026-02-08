#!/usr/bin/env python3
"""Quick test to check if firmware responds"""
import serial
import time

PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

try:
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2)
    print("Connected!")
    
    # Test encoder read command
    ser.write(b"e\r")
    time.sleep(0.1)
    response = ser.readline().decode().strip()
    print(f"Encoder response: '{response}'")
    
    # Test baudrate command
    ser.write(b"b\r")
    time.sleep(0.1)
    response = ser.readline().decode().strip()
    print(f"Baudrate response: '{response}'")
    
    if response:
        print("\n✓ Firmware responds - communication OK")
        
        # Check which pins are defined in firmware
        print("\n--- Pin Test ---")
        print("Testing GP6 (RIGHT_MOTOR_PWM in firmware)...")
        
        # Configure GP6 as OUTPUT
        ser.write(b"c 6 1\r")
        time.sleep(0.1)
        print(f"Config response: '{ser.readline().decode().strip()}'")
        
        # Set GP6 PWM to 200
        ser.write(b"x 6 200\r")
        time.sleep(0.1)
        print(f"PWM response: '{ser.readline().decode().strip()}'")
        
        input("\nMotor should be running. Press Enter...")
        
        # Stop
        ser.write(b"x 6 0\r")
        time.sleep(0.1)
        print("Stopped")
        
    else:
        print("\n✗ No response - firmware problem!")
    
    ser.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
