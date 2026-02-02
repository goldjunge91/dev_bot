/*
 * Nerf Launcher Firmware for Arduino Pro Micro (Brushless ESC Version)
 *
 * Hardware Mapping:
 * - Tilt Servo: Pin 10 (Standard Servo)
 * - Pusher Servo: Pin 9 (Continuous Servo or Standard)
 * - Flywheel Left: Pin 5 (ESC - Servo Signal)
 * - Flywheel Right: Pin 6 (ESC - Servo Signal)
 *
 * Serial Protocol (115200 baud):
 * - ARM:           Arm the system (Required before SHOT/ESC)
 * - DISARM:        Disarm system (Safe mode)
 * - SHOT <power>:  Fire sequence (0-80, default 40)
 * - ESC <power>:   Set Flywheel Speed (0-80)
 * - TILT <angle>:  Set Tilt Servo (0-180)
 * - STOP:          Emergency Stop
 * - STATUS:        Get Armed Status
 */

#include <Arduino.h>
#include <Servo.h>
#include <avr/wdt.h> // Watchdog timer for safety
#include <stdio.h>

// =============================================================================
// PIN DEFINITIONS
// =============================================================================
const int PIN_FLYWHEEL_L = 5;   // ESC Motor 1
const int PIN_FLYWHEEL_R = 6;   // ESC Motor 2
const int PIN_SERVO_PUSHER = 9; // Shot Servo
const int PIN_SERVO_TILT = 10;  // Tilt Servo

// =============================================================================
// ESC & TIMING CONFIGURATION
// =============================================================================
#define ESC_MIN_US 1000      // 0% throttle
#define ESC_FULL_US 2000     // 100% throttle (hardware max)
#define ESC_MAX_US 1800      // 80% throttle (safety limit!)
#define ESC_ARM_US 1000      // Arm signal
#define ESC_DEFAULT_POWER 40 // Default power for SHOT command

#define ESC_ARM_DELAY_MS 2000      // Time to arm ESCs
#define ESC_SPINUP_DELAY_MS 1500   // Time for flywheels to reach speed
#define SHOT_ROTATION_MS_FULL 1000 // Time for 360° at FULL speed (180)
// Note: Actual rotation time is calculated based on pusher speed

#define AUTO_DISARM_MS 60000 // Auto-disarm after 60 seconds of inactivity

// --- TILT SERVO (Position Servo - controls aiming angle) ---
#define SERVO_TILT_MIN_US 544    // Extended range for finer positioning
#define SERVO_TILT_MAX_US 2400   // Extended range (standard would be 1000-2000)
#define SERVO_TILT_MIN_ANGLE 90  // Software limit: minimum tilt angle
#define SERVO_TILT_MAX_ANGLE 125 // Software limit: maximum tilt angle

// --- PUSHER SERVO (Continuous Rotation Servo) ---
// How it works: 90=STOP, 91-180=forward (faster), 0-89=reverse
#define SERVO_PUSHER_MIN_US 1000       // PWM pulse range
#define SERVO_PUSHER_MAX_US 2000       // PWM pulse range
#define SERVO_PUSHER_STOP 90           // Neutral = motor stopped
#define SERVO_PUSHER_MIN_SPEED 91      // Slowest forward speed
#define SERVO_PUSHER_MAX_SPEED 180     // Fastest forward speed
#define SERVO_PUSHER_DEFAULT_SPEED 150 // Default speed

// =============================================================================
// COMMUNICATION
// =============================================================================
#define DEBUG_UART Serial1 // TX1/D1, RX1/D0 → USB-TTL adapter
#define USB_SERIAL Serial  // USB CDC → Raspberry Pi
#define BAUD_RATE 115200
// const long BAUD_RATE = 115200;
// =============================================================================
// FIRING STATE MACHINE
// =============================================================================
enum FiringState { IDLE, SPINNING_UP, PUSHING, COOLDOWN };

class Launcher {
private:
  Servo tiltServo;
  Servo pusherServo;
  Servo escLeft;
  Servo escRight;

  bool isArmed = false;
  bool tiltAttached = false;   // Lazy init
  bool pusherAttached = false; // Lazy init
  bool escsAttached = false;   // Lazy init

  // Non-blocking firing state machine
  FiringState firingState = IDLE;
  unsigned long stateStartTime = 0;
  int currentPower = 0;
  int pusherSpeed = SERVO_PUSHER_DEFAULT_SPEED; // Configurable pusher speed
  int pusherStopValue = SERVO_PUSHER_STOP;      // Calibratable stop value
  unsigned long currentRotationTime = 0;        // Calculated based on speed

  // Activity tracking for auto-disarm
  unsigned long lastActivityTime = 0;

public:
  // =============================================================================
  // HELPER FUNCTIONS
  // =============================================================================

  /**
   * Print message to both serial interfaces (PROGMEM optimized)
   */
  void debugPrint(const __FlashStringHelper *msg) {
    DEBUG_UART.println(msg);
    USB_SERIAL.println(msg);
  }

  // Overload for regular char* (runtime strings)
  void debugPrint(const char *msg) {
    DEBUG_UART.println(msg);
    USB_SERIAL.println(msg);
  }

  /**
   * Print formatted message with value
   */
  void debugPrintf(const char *format, int value) {
    char buf[64];
    sprintf(buf, format, value);
    DEBUG_UART.println(buf);
    USB_SERIAL.println(buf);
  }

  // Record activity for auto-disarm timeout
  void recordActivity() { lastActivityTime = millis(); }
  void begin() {
    // NOTHING attached here - all lazy initialized on first use
    // This prevents any servo movement on boot

    // Initialize activity timer
    lastActivityTime = millis();

    // Initial message
    debugPrint(F("Nerf Launcher Ready - Send HELP for commands"));
  }

  // Lazy attach ESCs (called before any ESC operation)
  void ensureEscsAttached() {
    if (!escsAttached) {
      escLeft.attach(PIN_FLYWHEEL_L, ESC_MIN_US, ESC_FULL_US);
      escRight.attach(PIN_FLYWHEEL_R, ESC_MIN_US, ESC_FULL_US);
      escsAttached = true;
    }
  }

  // Lazy attach pusher (called before any pusher operation)
  void ensurePusherAttached() {
    if (!pusherAttached) {
      pusherServo.attach(PIN_SERVO_PUSHER, SERVO_PUSHER_MIN_US,
                         SERVO_PUSHER_MAX_US);
      pusherServo.write(pusherStopValue); // Use calibrated stop value
      pusherAttached = true;
    }
  }

  void arm() {
    if (isArmed) {
      debugPrint(F("WARN: Already armed"));
      return;
    }

    // Lazy attach ESCs and pusher
    ensureEscsAttached();
    ensurePusherAttached();

    debugPrint(F("Arming system..."));
    // Arming sequence for ESCs
    escLeft.writeMicroseconds(ESC_ARM_US);
    escRight.writeMicroseconds(ESC_ARM_US);
    delay(ESC_ARM_DELAY_MS);

    isArmed = true;
    recordActivity();
    debugPrint(F("OK: ARMED"));
  }

  void disarm() {
    // Cancel any ongoing firing sequence
    firingState = IDLE;
    isArmed = false;

    // Only write to servos if they are attached
    if (escsAttached) {
      escLeft.writeMicroseconds(ESC_ARM_US);
      escRight.writeMicroseconds(ESC_ARM_US);
    }
    if (pusherAttached) {
      pusherServo.write(pusherStopValue); // Use calibrated stop value
    }
    debugPrint(F("OK: DISARMED"));
  }

  void setTilt(int angle) {
    // Lazy attach to prevent startup movement
    if (!tiltAttached) {
      tiltServo.attach(PIN_SERVO_TILT, SERVO_TILT_MIN_US, SERVO_TILT_MAX_US);
      tiltAttached = true;
    }
    // Input validation with configurable limits
    if (angle < SERVO_TILT_MIN_ANGLE || angle > SERVO_TILT_MAX_ANGLE) {
      debugPrint(F("ERR: Angle out of range"));
      return;
    }
    tiltServo.write(angle);
    debugPrintf("OK: Tilt=%d", angle);
  }

  // Direct control if needed, but fireShot is preferred
  void setPusher(int val) {
    if (!isArmed) {
      debugPrint(F("ERR: Must ARM first"));
      return;
    }
    if (val < 0 || val > 180) {
      debugPrint(F("ERR: Pusher must be 0-180"));
      return;
    }
    ensurePusherAttached();
    pusherServo.write(val);
    recordActivity();
    debugPrint(F("OK: Pusher"));
  }

  // Manual ESC control
  void setFlywheels(int val_l, int val_r) {
    if (!isArmed) {
      debugPrint(F("ERR: Must ARM first"));
      return;
    }

    // Input validation
    if (val_l < 0 || val_l > 100 || val_r < 0 || val_r > 100) {
      debugPrint(F("ERR: ESC values must be 0-100"));
      return;
    }

    int us_l = map(val_l, 0, 100, ESC_MIN_US, ESC_FULL_US);
    us_l = constrain(us_l, ESC_MIN_US, ESC_MAX_US); // Safety limit

    int us_r = map(val_r, 0, 100, ESC_MIN_US, ESC_FULL_US);
    us_r = constrain(us_r, ESC_MIN_US, ESC_MAX_US);

    escLeft.writeMicroseconds(us_l);
    escRight.writeMicroseconds(us_r);
    recordActivity();
  }

  // Fire Sequence - Non-blocking initiation
  void fireShot(int powerPercent = ESC_DEFAULT_POWER) {
    if (!isArmed) {
      debugPrint(F("ERR: Not armed! Send ARM first"));
      return;
    }

    if (firingState != IDLE) {
      debugPrint(F("ERR: Already firing"));
      return;
    }

    // Input validation
    if (powerPercent < 0 || powerPercent > 80) {
      debugPrint(F("ERR: Power must be 0-80"));
      return;
    }

    currentPower = powerPercent;
    debugPrintf("OK: FIRE at %d%%", currentPower);

    // Start spin-up phase
    setFlywheelsInternal(currentPower, currentPower);
    debugPrint(F("Spinning up..."));
    firingState = SPINNING_UP;
    stateStartTime = millis();
    recordActivity();
  }

  // Internal flywheel control (bypasses armed check for state machine)
  void setFlywheelsInternal(int val_l, int val_r) {
    int us_l = map(constrain(val_l, 0, 100), 0, 100, ESC_MIN_US, ESC_FULL_US);
    us_l = constrain(us_l, ESC_MIN_US, ESC_MAX_US);

    int us_r = map(constrain(val_r, 0, 100), 0, 100, ESC_MIN_US, ESC_FULL_US);
    us_r = constrain(us_r, ESC_MIN_US, ESC_MAX_US);

    escLeft.writeMicroseconds(us_l);
    escRight.writeMicroseconds(us_r);
  }

  // Non-blocking state machine update - call from loop()
  void update() {
    unsigned long now = millis();
    unsigned long elapsed = now - stateStartTime;

    // Check for auto-disarm timeout
    if (isArmed && firingState == IDLE) {
      if (now - lastActivityTime > AUTO_DISARM_MS) {
        debugPrint(F("WARN: Auto-disarm (timeout)"));
        disarm();
      }
    }

    switch (firingState) {
    case IDLE:
      // Nothing to do
      break;

    case SPINNING_UP:
      if (elapsed >= ESC_SPINUP_DELAY_MS) {
        // Calculate rotation time based on speed
        // Speed 180 = base time, slower speeds take proportionally longer
        int speedRange = SERVO_PUSHER_MAX_SPEED - SERVO_PUSHER_STOP; // 90
        int currentSpeedOffset =
            pusherSpeed - SERVO_PUSHER_STOP; // e.g., 60 for speed 150
        currentRotationTime = (unsigned long)SHOT_ROTATION_MS_FULL *
                              speedRange / currentSpeedOffset;

        debugPrintf("Pushing at speed %d...", pusherSpeed);
        pusherServo.write(pusherSpeed);
        firingState = PUSHING;
        stateStartTime = millis();
      }
      break;

    case PUSHING:
      if (elapsed >= currentRotationTime) {
        // Stop pusher and flywheels
        pusherServo.write(pusherStopValue);
        setFlywheelsInternal(0, 0);
        debugPrint(F("OK: FIRE complete"));
        firingState = IDLE;
        recordActivity();
      }
      break;

    case COOLDOWN:
      // Reserved for future use (e.g., burst fire delay)
      firingState = IDLE;
      break;
    }
  }

  // Check if currently firing
  bool isFiring() { return firingState != IDLE; }

  // Cancel firing sequence (emergency stop)
  void cancelFiring() {
    if (firingState != IDLE) {
      pusherServo.write(pusherStopValue);
      setFlywheelsInternal(0, 0);
      firingState = IDLE;
      debugPrint(F("OK: Firing cancelled"));
    }
  }

  // Set pusher speed (91-180, higher = faster)
  void setPusherSpeed(int speed) {
    if (speed < SERVO_PUSHER_MIN_SPEED || speed > SERVO_PUSHER_MAX_SPEED) {
      debugPrint(F("ERR: Speed must be 91-180"));
      return;
    }
    pusherSpeed = speed;
    debugPrintf("OK: Pusher speed=%d", pusherSpeed);
  }

  int getPusherSpeed() { return pusherSpeed; }

  // Test pusher with X full rotations (for debugging)
  void testPusher(int rotations) {
    if (rotations < 1 || rotations > 10) {
      debugPrint(F("ERR: Rotations must be 1-10"));
      return;
    }
    ensurePusherAttached();

    // Start pusher at current speed
    pusherServo.write(pusherSpeed);

    // Calculate total time for X rotations
    unsigned long rotationTime = currentRotationTime * rotations;
    delay(rotationTime);

    // Stop pusher
    pusherServo.write(pusherStopValue);
    debugPrintf("OK: Pusher %d rotations complete", rotations);
  }

  // Calibrate pusher stop value (find exact stop point)
  void calibratePusherStop(int val) {
    if (val < 80 || val > 100) {
      debugPrint(F("ERR: Stop value must be 80-100"));
      return;
    }
    pusherStopValue = val;
    ensurePusherAttached();
    pusherServo.write(pusherStopValue);
    debugPrintf("OK: Pusher stop calibrated to %d", pusherStopValue);
  }

  int getPusherStopValue() { return pusherStopValue; }

  // Stop pusher immediately
  void stopPusher() {
    if (!pusherAttached) {
      debugPrint(F("WARN: Pusher not attached"));
      return;
    }
    pusherServo.write(pusherStopValue);
    debugPrintf("OK: Pusher stopped at %d", pusherStopValue);
  }

  bool getArmed() { return isArmed; }
};

class SerialComms {
private:
  Launcher &launcher;
  Stream &stream;
  String inputBuffer;

public:
  SerialComms(Launcher &l, Stream &s) : launcher(l), stream(s) {
    inputBuffer.reserve(32);
  }

  void update() {
    while (stream.available()) {
      char c = stream.read();
      if (c == '\n' || c == '\r') {
        if (inputBuffer.length() > 0) {
          processCommand(inputBuffer);
          inputBuffer = "";
        }
      } else if (c >= 32 && c <= 126) { // Only printable ASCII
        inputBuffer += c;
      }
      // Ignore non-printable characters
    }
  }

  void processCommand(String cmd) {
    cmd.trim();

    // Ignore empty commands
    if (cmd.length() == 0) {
      return;
    }

    cmd.toUpperCase();

    // Ignore echo messages (prevent infinite loops)
    if (cmd.startsWith("ERR:") || cmd.startsWith("OK:") ||
        cmd.startsWith("WARN:") || cmd.startsWith("STATUS:")) {
      return;
    }

    if (cmd == "ARM") {
      launcher.arm();
    } else if (cmd == "DISARM") {
      launcher.disarm();
    } else if (cmd.startsWith("TILT ")) {
      int angle = cmd.substring(5).toInt();
      launcher.setTilt(angle);
    } else if (cmd.startsWith("ESC ")) {
      int speed = cmd.substring(4).toInt();
      launcher.setFlywheels(speed, speed);
      launcher.debugPrintf("OK: ESC=%d", speed);
    } else if (cmd.startsWith("SHOT")) {
      int speed = ESC_DEFAULT_POWER;
      if (cmd.length() > 5) {
        speed = cmd.substring(5).toInt();
      }
      launcher.fireShot(speed);
    } else if (cmd.startsWith("F ")) {
      // Individual flywheel control: "F <left> <right>"
      int spaceIdx = cmd.indexOf(' ', 2);
      if (spaceIdx != -1) {
        int val_l = cmd.substring(2, spaceIdx).toInt();
        int val_r = cmd.substring(spaceIdx + 1).toInt();
        launcher.setFlywheels(val_l, val_r);
        launcher.debugPrint(F("OK: Flywheels"));
      } else {
        launcher.debugPrint(F("ERR: Usage: F <left> <right>"));
      }
    } else if (cmd == "STOP") {
      launcher.disarm();
    } else if (cmd.startsWith("PSPEED ")) {
      // Set pusher speed: "PSPEED <speed>" (91-180)
      int speed = cmd.substring(7).toInt();
      launcher.setPusherSpeed(speed);
    } else if (cmd.startsWith("PUSHER ")) {
      // Test pusher: "PUSHER <value>" (90=stop, 91-180=forward)
      int val = cmd.substring(7).toInt();
      launcher.testPusher(val);
    } else if (cmd.startsWith("PCAL ")) {
      // Calibrate pusher stop: "PCAL <value>" (80-100, usually ~87-93)
      int val = cmd.substring(5).toInt();
      launcher.calibratePusherStop(val);
    } else if (cmd == "PSTOP") {
      // Stop pusher immediately
      launcher.stopPusher();
    } else if (cmd == "STATUS") {
      if (launcher.getArmed())
        launcher.debugPrint(F("STATUS: ARMED"));
      else
        launcher.debugPrint(F("STATUS: DISARMED"));
    } else if (cmd == "HELP") {
      launcher.debugPrint(
          F("Commands: ARM DISARM SHOT TILT<angle> ESC<speed> "
            "PUSHER<rotations> PCAL<val> PSPEED<speed> STATUS"));
    } else if (cmd.length() > 0) {
      // Only show error for non-empty commands
      launcher.debugPrintf("ERR: Unknown '%s'", cmd.c_str());
    }
  }
};

// =============================================================================
// MAIN PROGRAM
// =============================================================================

Launcher nerfLauncher;
SerialComms usbComms(nerfLauncher, USB_SERIAL);
SerialComms uartComms(nerfLauncher, DEBUG_UART);

void setup() {
  // Disable watchdog during setup (in case of reset loop)
  wdt_disable();

  USB_SERIAL.begin(BAUD_RATE);
  DEBUG_UART.begin(BAUD_RATE);
  nerfLauncher.begin();

  pinMode(LED_BUILTIN, OUTPUT);
  // Blink 3 times to signal ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }

  // Watchdog disabled - was causing upload issues
  // wdt_enable(WDTO_2S);
}

void loop() {
  // Watchdog disabled
  // wdt_reset();

  // Update firing state machine (non-blocking)
  nerfLauncher.update();

  // Process serial commands
  usbComms.update();
  uartComms.update();
}
