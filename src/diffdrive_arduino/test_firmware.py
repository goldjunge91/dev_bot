#!/usr/bin/env python3
"""
Test script to verify Pico firmware communication and pin configuration
"""
import serial
import time

PORT = "/dev/serial/by-id/usb-Raspberry_Pi_Pico_5033592712D0351F-if00"
BAUD = 57600

def send_command(ser, cmd):
    """Send command and get response"""
    ser.write(f"{cmd}\r".encode())
    time.sleep(0.1)
    response = ser.readline().decode().strip()
    return response

print("=" * 60)
print("RASPBERRY PI PICO FIRMWARE TEST")
print("=" * 60)

try:
    # Connect to Pico
    print(f"\n1. Connecting to {PORT}...")
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2)
    print("   ✓ Connected!")
    
    # Test basic communication
    print("\n2. Testing communication with 'e' (read encoders) command...")
    response = send_command(ser, "e")
    print(f"   Response: '{response}'")
    if response:
        print("   ✓ Communication working!")
    else:
        print("   ✗ No response - check firmware!")
        ser.close()
        exit(1)
    
    # Test current pin configuration
    print("\n3. Current firmware pin configuration:")
    print("   LEFT Motor:  GP0 (PWM), GP4 (IN1), GP5 (IN2)")
    print("   RIGHT Motor: GP6 (PWM), GP7 (IN1), GP8 (IN2)")
    print("   LEFT Enc:    GP22 (A), GP21 (B)")
    print("   RIGHT Enc:   GP11 (A), GP10 (B)")
    
    # Check where motors are actually wired
    print("\n4. Testing which pins have motors connected...")
    print("   This will briefly activate each pin to detect motors.\n")
    
    test_configs = [
        ("OLD LEFT (GP2,3,4)", 2, 3, 4),
        ("NEW LEFT (GP0,4,5)", 0, 4, 5),
        ("RIGHT (GP6,7,8)", 6, 7, 8),
    ]
    
    for name, pwm, in1, in2 in test_configs:
        print(f"   Testing {name}...")
        
        # Configure pins
        send_command(ser, f"c {pwm} 1")
        send_command(ser, f"c {in1} 1")
        send_command(ser, f"c {in2} 1")
        
        # Set direction
        send_command(ser, f"w {in1} 1")
        send_command(ser, f"w {in2} 0")
        
        # Brief PWM pulse
        send_command(ser, f"x {pwm} 150")
        time.sleep(0.5)
        send_command(ser, f"x {pwm} 0")
        
        # Disable
        send_command(ser, f"w {in1} 0")
        send_command(ser, f"w {in2} 0")
        
        input(f"   Did motor spin? (Press Enter to continue)")
        time.sleep(0.3)
    
    print("\n5. Important notes:")
    print("   • TB6612 STBY pin must be connected to 3.3V (always enabled)")
    print("   • Or connect STBY to a GPIO and set it HIGH in firmware")
    print("   • Motors must be wired to the NEW pin configuration")
    print("   • Check motor power supply is connected and adequate")
    
    ser.close()
    print("\n✓ Test complete!")
    
except serial.SerialException as e:
    print(f"\n✗ Serial port error: {e}")
    print("   Check if Pico is connected and no other program is using the port")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
