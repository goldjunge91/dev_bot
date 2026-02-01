/**
 * Nerf Launcher Controller - Arduino Pro Micro (ATmega32U4)
 * 
 * Controls a Nerf dart launcher with:
 * - 2x ESC for flywheel motors (0-80% max)
 * - 1x 360° continuous servo for dart pusher
 * - 1x Standard servo for tilt (up/down)
 * 
 * Communication:
 * - UART (Serial1, TX1/RX1): Debug via USB-TTL adapter
 * - USB (Serial): Production with Raspberry Pi / micro-ROS
 * 
 * Commands:
 *   ARM           - Arm the system (required before SHOT/ESC)
 *   DISARM        - Disarm the system (safe)
 *   SHOT [speed]  - Fire sequence with optional power 0-80% (default: 40%)
 *   ESC <speed>   - Manual ESC control 0-80% (only when armed)
 *   TILT <angle>  - Set tilt angle 0-180°
 *   STOP          - Emergency stop + disarm
 *   STATUS        - Get current armed state
 * 
 * Pin Map (see docs/doc/PINMAP_NERF.md):
 *   D2 - ESC Motor 1 (left flywheel)
 *   D3 - ESC Motor 2 (right flywheel)
 *   D4 - Shot Servo (360° continuous)
 *   D5 - Tilt Servo (0-180°)
 * 
 * Author: goldjunge91
 * Date: 2026-01-26
 */

#include <Servo.h>

// =============================================================================
// PIN DEFINITIONS
// =============================================================================
#define ESC_MOTOR_1_PIN   2
#define ESC_MOTOR_2_PIN   3
#define SHOT_SERVO_PIN    4
#define TILT_SERVO_PIN    5

// =============================================================================
// ESC CONFIGURATION
// =============================================================================
#define ESC_MIN_US        1000  // 0% throttle
#define ESC_MAX_US        1800  // 80% throttle (safety limit!)
#define ESC_ARM_US        1000  // Arm signal
#define ESC_DEFAULT_POWER 40    // Default power for SHOT command

// =============================================================================
// TIMING CONFIGURATION (adjust for your hardware)
// =============================================================================
#define ESC_ARM_DELAY_MS     2000  // Time to arm ESCs
#define ESC_SPINUP_DELAY_MS  1500  // Time for flywheels to reach speed
#define SHOT_ROTATION_MS     1000  // Time for 360° servo full rotation

// =============================================================================
// COMMUNICATION
// =============================================================================
#define DEBUG_UART        Serial1  // TX1/D1, RX1/D0 → USB-TTL adapter
#define USB_SERIAL        Serial   // USB CDC → Raspberry Pi
#define BAUD_RATE         115200

// =============================================================================
// GLOBAL VARIABLES
// =============================================================================
Servo esc1, esc2;
Servo shotServo;
Servo tiltServo;

bool isArmed = false;

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Print message to both serial interfaces
 */
void debugPrint(const char* msg) {
    DEBUG_UART.println(msg);
    USB_SERIAL.println(msg);
}

/**
 * Print formatted message with value
 */
void debugPrintf(const char* format, int value) {
    char buf[64];
    sprintf(buf, format, value);
    debugPrint(buf);
}

// =============================================================================
// SYSTEM CONTROL
// =============================================================================

/**
 * Arm the system - required before firing
 */
void armSystem() {
    if (isArmed) {
        debugPrint("Already armed!");
        return;
    }
    
    debugPrint("Arming system...");
    esc1.writeMicroseconds(ESC_ARM_US);
    esc2.writeMicroseconds(ESC_ARM_US);
    delay(ESC_ARM_DELAY_MS);
    
    isArmed = true;
    debugPrint("ARMED - ready to fire!");
}

/**
 * Disarm the system - safe state
 */
void disarmSystem() {
    esc1.writeMicroseconds(ESC_ARM_US);
    esc2.writeMicroseconds(ESC_ARM_US);
    shotServo.write(90);  // Stop continuous servo
    isArmed = false;
    debugPrint("DISARMED - safe");
}

// =============================================================================
// MOTOR CONTROL
// =============================================================================

/**
 * Set ESC speed (0-80%)
 */
void setESCSpeed(int percent) {
    percent = constrain(percent, 0, 80);  // Safety: max 80%!
    int us = map(percent, 0, 100, ESC_MIN_US, 2000);
    us = constrain(us, ESC_MIN_US, ESC_MAX_US);
    
    esc1.writeMicroseconds(us);
    esc2.writeMicroseconds(us);
}

/**
 * Execute complete fire sequence
 * @param escSpeed ESC power 0-80% (default: 40%)
 */
void fireShot(int escSpeed = ESC_DEFAULT_POWER) {
    if (!isArmed) {
        debugPrint("ERROR: Not armed! Send ARM first.");
        return;
    }
    
    escSpeed = constrain(escSpeed, 0, 80);
    debugPrintf("FIRE at %d%% power...", escSpeed);
    
    // 1. Spin up flywheels
    setESCSpeed(escSpeed);
    debugPrint("ESCs spinning up...");
    delay(ESC_SPINUP_DELAY_MS);
    
    // 2. Push dart (360° servo full rotation)
    debugPrint("Pushing dart...");
    shotServo.write(180);  // Full speed forward
    delay(SHOT_ROTATION_MS);
    shotServo.write(90);   // Stop
    
    // 3. Stop flywheels
    setESCSpeed(0);
    debugPrint("FIRE complete!");
}

/**
 * Set tilt servo angle
 */
void setTiltAngle(int angle) {
    angle = constrain(angle, 0, 180);
    tiltServo.write(angle);
    debugPrintf("Tilt set to %d degrees", angle);
}

// =============================================================================
// COMMAND PROCESSING
// =============================================================================

/**
 * Process incoming command string
 */
void processCommand(String cmd) {
    cmd.trim();
    cmd.toUpperCase();
    
    if (cmd == "ARM") {
        armSystem();
    } 
    else if (cmd == "DISARM") {
        disarmSystem();
    } 
    else if (cmd.startsWith("ESC ")) {
        if (!isArmed) {
            debugPrint("ERROR: Not armed!");
            return;
        }
        int speed = cmd.substring(4).toInt();
        setESCSpeed(speed);
        debugPrintf("ESC set to %d%%", speed);
    } 
    else if (cmd.startsWith("SHOT")) {
        int speed = ESC_DEFAULT_POWER;
        if (cmd.length() > 5) {
            speed = cmd.substring(5).toInt();
        }
        fireShot(speed);
    } 
    else if (cmd.startsWith("TILT ")) {
        int angle = cmd.substring(5).toInt();
        setTiltAngle(angle);
    } 
    else if (cmd == "STOP") {
        disarmSystem();
    } 
    else if (cmd == "STATUS") {
        debugPrint(isArmed ? "STATUS: ARMED" : "STATUS: DISARMED");
    }
    else if (cmd.length() > 0) {
        debugPrint("Unknown command. Available: ARM, DISARM, SHOT, ESC, TILT, STOP, STATUS");
    }
}

// =============================================================================
// SETUP & LOOP
// =============================================================================

void setup() {
    // Initialize serial interfaces
    USB_SERIAL.begin(BAUD_RATE);
    DEBUG_UART.begin(BAUD_RATE);
    
    // Wait for serial (optional, for debugging)
    delay(1000);
    
    // Attach servos
    esc1.attach(ESC_MOTOR_1_PIN, 1000, 2000);
    esc2.attach(ESC_MOTOR_2_PIN, 1000, 2000);
    shotServo.attach(SHOT_SERVO_PIN);
    tiltServo.attach(TILT_SERVO_PIN);
    
    // Initialize to safe state
    esc1.writeMicroseconds(ESC_ARM_US);
    esc2.writeMicroseconds(ESC_ARM_US);
    shotServo.write(90);   // Stop position for continuous servo
    tiltServo.write(90);   // Center position
    
    debugPrint("=================================");
    debugPrint("Nerf Launcher Controller Ready!");
    debugPrint("Commands: ARM, DISARM, SHOT [power], ESC <power>, TILT <angle>, STOP, STATUS");
    debugPrint("=================================");
}

void loop() {
    // Check UART (debug interface)
    if (DEBUG_UART.available()) {
        String cmd = DEBUG_UART.readStringUntil('\n');
        processCommand(cmd);
    }
    
    // Check USB (Raspberry Pi interface)
    if (USB_SERIAL.available()) {
        String cmd = USB_SERIAL.readStringUntil('\n');
        processCommand(cmd);
    }
}
