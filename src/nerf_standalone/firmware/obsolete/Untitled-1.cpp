/**
 * NERF OS PRO - Integrated Firmware
 * - Non-blocking State Machine für Schuss-Sequenz
 * - Kalibrierungs-Suite für 360° Servos (Shot & Tilt)
 * - Pro Micro Pinout: D2/D3 (ESC), D9 (Shot), D10 (Tilt)
 */

#include <Arduino.h>
#include <Servo.h>

// =============================================================================
// KONFIGURATION & PINS
// =============================================================================
const int PIN_ESC_L = 2;
const int PIN_ESC_R = 3;
const int PIN_SHOT = 9;
const int PIN_TILT = 10;

#define SV_MIN 500
#define SV_MAX 2500
#define SV_STOP 1500

#define ESC_MIN_US 1000
#define ESC_MAX_US 1800 // Safety Limit 80%
#define ESC_ARM_US 1000

#define SPINUP_MS 1200
#define AUTO_DISARM_MS 60000

// =============================================================================
// LAUNCHER LOGIK (STATE MACHINE)
// =============================================================================
enum FiringState { IDLE, SPINNING_UP, PUSHING };

class Launcher {
private:
  Servo escL, escR, shotServo, tiltServo;

  bool isArmed = false;
  FiringState state = IDLE;
  unsigned long stateStartTime = 0;
  unsigned long lastActivity = 0;

  // Kalibrierwerte
  int shotNeutralUs = 1500;
  int tiltNeutralUs = 1500;
  int shotDurationMs = 500;

public:
  void begin() {
    lastActivity = millis();
    // ESCs initialisieren
    escL.attach(PIN_ESC_L, 1000, 2000);
    escR.attach(PIN_ESC_R, 1000, 2000);
    stopFlywheels();
    Serial.println(F("OK: Nerf Launcher Ready. Type HELP."));
  }

  // --- HARDWARE STEUERUNG ---

  void stopFlywheels() {
    escL.writeMicroseconds(ESC_ARM_US);
    escR.writeMicroseconds(ESC_ARM_US);
  }

  void setFlywheels(int powerPercent) {
    int us = map(constrain(powerPercent, 0, 80), 0, 100, 1000, 2000);
    us = constrain(us, ESC_MIN_US, ESC_MAX_US);
    escL.writeMicroseconds(us);
    escR.writeMicroseconds(us);
  }

  void arm() {
    isArmed = true;
    stopFlywheels();
    lastActivity = millis();
    Serial.println(F("OK: ARMED"));
  }

  void disarm() {
    isArmed = false;
    state = IDLE;
    stopFlywheels();
    shotServo.detach();
    tiltServo.detach();
    Serial.println(F("OK: DISARMED"));
  }

  // --- TILT FUNKTIONEN (360°) ---

  void moveTilt(int speedUs, int duration) {
    tiltServo.attach(PIN_TILT, SV_MIN, SV_MAX);
    tiltServo.writeMicroseconds(speedUs);
    delay(duration); // Kurze Kalibrier-Moves dürfen blockieren
    tiltServo.writeMicroseconds(tiltNeutralUs);
    delay(50);
    tiltServo.detach();
    Serial.println(F("OK: Tilt moved"));
  }

  // --- SHOT / PUSHER FUNKTIONEN ---

  void nudgeShot(bool forward) {
    shotServo.attach(PIN_SHOT, SV_MIN, SV_MAX);
    int speed = forward ? (shotNeutralUs + 300) : (shotNeutralUs - 300);
    shotServo.writeMicroseconds(speed);
    delay(80); // Kurzer Impuls
    shotServo.writeMicroseconds(shotNeutralUs);
    delay(50);
    shotServo.detach();
    Serial.println(F("OK: Nudge done"));
  }

  void startFireSequence(int duration = 0) {
    if (!isArmed) {
      Serial.println(F("ERR: Not armed"));
      return;
    }
    if (state != IDLE)
      return;

    if (duration > 0)
      shotDurationMs = duration;

    setFlywheels(50); // Standard-Power
    state = SPINNING_UP;
    stateStartTime = millis();
    lastActivity = millis();
    Serial.println(F("OK: Fire sequence started"));
  }

  // --- KALIBRIERUNG ---

  void setZeroS(int us) {
    shotNeutralUs = us;
    Serial.print(F("Shot Neutral: "));
    Serial.println(us);
  }
  void setZeroT(int us) {
    tiltNeutralUs = us;
    Serial.print(F("Tilt Neutral: "));
    Serial.println(us);
  }
  void setShotDur(int ms) {
    shotDurationMs = ms;
    Serial.print(F("Shot Duration: "));
    Serial.println(ms);
  }

  void saveInfo() {
    Serial.println(F("\n--- CURRENT CALIBRATION ---"));
    Serial.print(F("ZERO_S "));
    Serial.println(shotNeutralUs);
    Serial.print(F("ZERO_T "));
    Serial.println(tiltNeutralUs);
    Serial.print(F("SET_SHOT "));
    Serial.println(shotDurationMs);
  }

  // --- MAIN UPDATE (NON-BLOCKING) ---

  void update() {
    unsigned long now = millis();

    // Auto-Disarm
    if (isArmed && state == IDLE && (now - lastActivity > AUTO_DISARM_MS)) {
      disarm();
      Serial.println(F("WARN: Auto-disarm"));
    }

    switch (state) {
    case SPINNING_UP:
      if (now - stateStartTime >= SPINUP_MS) {
        shotServo.attach(PIN_SHOT, SV_MIN, SV_MAX);
        shotServo.writeMicroseconds(SV_MAX); // Full Speed Forward
        state = PUSHING;
        stateStartTime = now;
      }
      break;

    case PUSHING:
      if (now - stateStartTime >= (unsigned long)shotDurationMs) {
        shotServo.writeMicroseconds(shotNeutralUs);
        delay(50);
        shotServo.detach();
        stopFlywheels();
        state = IDLE;
        Serial.println(F("OK: Shot complete"));
      }
      break;

    default:
      break;
    }
  }

  bool getArmed() { return isArmed; }
};

// =============================================================================
// SERIAL COMMUNICATION CLASS
// =============================================================================

class SerialComms {
private:
  Launcher &launcher;
  String buffer;

public:
  SerialComms(Launcher &l) : launcher(l) { buffer.reserve(32); }

  void update() {
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') {
        if (buffer.length() > 0) {
          process(buffer);
          buffer = "";
        }
      } else {
        buffer += c;
      }
    }
  }

  void process(String cmd) {
    cmd.trim();
    int spaceIdx = cmd.indexOf(' ');
    String action = (spaceIdx > -1) ? cmd.substring(0, spaceIdx) : cmd;
    action.toUpperCase();
    int val = (spaceIdx > -1) ? cmd.substring(spaceIdx + 1).toInt() : 0;

    if (action == "ARM")
      launcher.arm();
    else if (action == "DISARM" || action == "STOP")
      launcher.disarm();
    else if (action == "SHOT")
      launcher.startFireSequence(val);
    else if (action == "NF")
      launcher.nudgeShot(true);
    else if (action == "NB")
      launcher.nudgeShot(false);
    else if (action == "UP")
      launcher.moveTilt(SV_MAX, val > 0 ? val : 200);
    else if (action == "DN")
      launcher.moveTilt(SV_MIN, val > 0 ? val : 200);
    else if (action == "ZERO_S")
      launcher.setZeroS(val);
    else if (action == "ZERO_T")
      launcher.setZeroT(val);
    else if (action == "SET_SHOT")
      launcher.setShotDur(val);
    else if (action == "SAVE")
      launcher.saveInfo();
    else if (action == "STATUS")
      Serial.println(launcher.getArmed() ? "ARMED" : "DISARMED");
    else if (action == "HELP") {
      Serial.println(F("Commands: ARM, DISARM, SHOT <ms>, UP/DN <ms>, NF/NB, "
                       "ZERO_S/T, SAVE, HELP"));
    }
  }
};

// =============================================================================
// MAIN EXECUTION
// =============================================================================

Launcher nerf;
SerialComms comms(nerf);

void setup() {
  Serial.begin(115200);
  while (!Serial)
    ; // Pro Micro Sync
  nerf.begin();
}

void loop() {
  nerf.update();  // State Machine Update
  comms.update(); // Serial Processing
}