#ifndef LAUNCHER_H
#define LAUNCHER_H

#include "Config.h"
#include <Arduino.h>
#include <Servo.h>

enum class FiringState {
  IDLE,
  ARMING,
  SPINNING_UP,
  PUSHING,
  BRAKING,
  COOLDOWN,
  ESC_TEST
};

class Launcher {
private:
  Servo _escL, _escR, _shot;

  FiringState _fState = FiringState::IDLE;

  bool _isArmed = false;
  uint32_t _stateStartTime = 0;
  uint32_t _lastActivityTime = 0;

  // Calibration Values
  int shotNeutralUs = Config::SHOT_NEUTRAL_DEFAULT;
  int shotDurationMs = Config::SHOT_DURATION_DEFAULT;

  void applyFlywheelPower(int powerPercent) {
    int powerLimit = constrain(powerPercent, 0, 100);
    int usL = Config::INV_L
                  ? map(powerLimit, 0, 100, Config::ESC_MID, Config::ESC_MIN)
                  : map(powerLimit, 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    int usR = Config::INV_R
                  ? map(powerLimit, 0, 100, Config::ESC_MID, Config::ESC_MIN)
                  : map(powerLimit, 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    _escL.writeMicroseconds(usL);
    _escR.writeMicroseconds(usR);
  }

public:
  Launcher() {} // No tilt init

  void begin() { _lastActivityTime = millis(); }

  // --- HELPER OUTPUT ---
  void debugPrint(const __FlashStringHelper *msg) {
    Serial.println(msg);
    Serial1.println(msg);
  }
  void debugPrintf(const char *format, int value) {
    char buf[64];
    sprintf(buf, format, value);
    Serial.println(buf);
    Serial1.println(buf);
  }

  bool isArmed() { return _isArmed; }

  // --- ARMING ---
  void arm() {
    if (_isArmed || _fState == FiringState::ARMING)
      return;

    // Attach ESCs ONLY. Pusher stays detached for safety!
    _escL.attach(Config::PIN_FLY_L, Config::ESC_MIN, Config::ESC_MAX);
    _escR.attach(Config::PIN_FLY_R, Config::ESC_MIN, Config::ESC_MAX);
    applyFlywheelPower(0); // Arm with 0% power (Stop/Arm signal)

    _fState = FiringState::ARMING;
    _stateStartTime = millis();
    _lastActivityTime = millis();
    debugPrint(F("STATUS: ARMING sequence started (2s)..."));
  }

  void disarm() {
    _isArmed = false;
    _fState = FiringState::IDLE;

    // Detach ESCs to trigger "Signal Lost" beep (Audio feedback)
    if (_escL.attached())
      _escL.detach();
    if (_escR.attached())
      _escR.detach();

    _shot.detach();
    // Tilt detach handled by TiltController elsewhere
    debugPrint(F("OK: SYSTEM DISARMED (Signal Cut)"));
  }

  // --- MANUAL ACTIONS ---

  void testEsc(int pwr) {
    if (!_isArmed) {
      debugPrint(F("ERR: Arm first!"));
      return;
    }
    applyFlywheelPower(pwr);
    _fState = FiringState::ESC_TEST;
    debugPrintf("OK: Flywheels spinning at %d%%. Send STOP to end.", pwr);
    _lastActivityTime = millis();
  }

  void testShot(int ms) {
    int duration = (ms > 0) ? ms : shotDurationMs;
    debugPrintf("OK: Test shot %d ms", duration);

    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    _shot.writeMicroseconds(shotNeutralUs + Config::SHOT_SPEED_OFFSET);

    delay(duration);

    // Active Brake
    _shot.writeMicroseconds(shotNeutralUs - Config::BRAKE_OFFSET);
    delay(Config::BRAKE_MS);
    _shot.writeMicroseconds(shotNeutralUs);
    delay(50);
    _shot.detach();
    recordActivity();
  }

  void nudge(bool forward) {
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    int s = forward ? (shotNeutralUs + 300) : (shotNeutralUs - 300);
    _shot.writeMicroseconds(s);
    delay(100);
    _shot.writeMicroseconds(shotNeutralUs);
    delay(50);
    _shot.detach();

    char buf[64];
    sprintf(buf, "OK: Nudge %s (Signal: %d)", forward ? "Fwd" : "Back", s);
    Serial.println(buf);
    Serial1.println(buf);

    _lastActivityTime = millis();
  }

  void setRawPWM(int us) {
    if (!_escL.attached()) {
      _escL.attach(Config::PIN_FLY_L, Config::ESC_MIN, Config::ESC_MAX);
      _escR.attach(Config::PIN_FLY_R, Config::ESC_MIN, Config::ESC_MAX);
    }
    _escL.writeMicroseconds(us);
    _escR.writeMicroseconds(us);
    debugPrintf("OK: Manual PWM %d us", us);
  }

  void startCalibration() {
    if (!_escL.attached()) {
      _escL.attach(Config::PIN_FLY_L, Config::ESC_MIN, Config::ESC_MAX);
      _escR.attach(Config::PIN_FLY_R, Config::ESC_MIN, Config::ESC_MAX);
    }
    _escL.writeMicroseconds(Config::ESC_MAX);
    _escR.writeMicroseconds(Config::ESC_MAX);
    debugPrint(F("WARNING: CALIBRATION MODE - MAX THROTTLE (2000us)"));
    debugPrint(F("1. Connect Battery NOW (Wait for Beep-Beep)"));
    debugPrint(F("2. Type 'STOP' immediately after beeps to finish"));
  }

  void startFire(int pwr) {
    if (!_isArmed) {
      debugPrint(F("ERR: Arm first!"));
      return;
    }
    if (_fState != FiringState::IDLE)
      return;

    applyFlywheelPower(pwr);

    _fState = FiringState::SPINNING_UP;
    _stateStartTime = millis();
    recordActivity();
    debugPrint(F("STATUS: Spinning up..."));
  }

  // --- CONFIG SETTERS ---
  void setZS(int v) {
    shotNeutralUs = v;
    debugPrintf("OK: Shot Zero set to %d", v);
  }

  void setD(int v) {
    shotDurationMs = v;
    debugPrintf("OK: Duration set to %d", v);
  }

  void printConfig() {
    debugPrint(F("\n--- CURRENT CONFIG ---"));
    debugPrintf("Shot Zero:     %d us", shotNeutralUs);
    // Tilt Zero removed from here
    debugPrintf("Shot Duration: %d ms", shotDurationMs);
    debugPrint(F("----------------------"));
  }

  void printHelp() {
    debugPrint(F("\n--- COMMAND LIST ---"));
    debugPrint(F(" > ARM / DISARM      - Safety Control"));
    debugPrint(F(" > SHOT <pwr>        - Fire Sequence (0-80)"));
    debugPrint(F(" > TEST_ESC <pwr>    - Test Flywheels"));
    debugPrint(F(" > PWM <us>          - Manual ESC Signal"));
    debugPrint(F(" > CAL               - Calibrate ESCs"));
    debugPrint(F(" > NF / NB           - Nudge Shot Fwd/Back"));
    debugPrint(F(" > TEST_SHOT <ms>    - Test Pusher Only"));
    debugPrint(F(" > UP / DN <ms>      - Tilt Move"));
    debugPrint(F(" > ZERO_S / ZERO_T   - Neutral points"));
    debugPrint(F(" > SET_SHOT <ms>     - Set Shot Duration"));
    debugPrint(F(" > SAVE              - Show Config"));
    debugPrint(F("--------------------"));
  }

  void recordActivity() { _lastActivityTime = millis(); }

  // --- UPDATE LOOP ---
  void update() {
    uint32_t now = millis();

    // Auto-Disarm
    if (_isArmed && _fState == FiringState::IDLE &&
        (now - _lastActivityTime > Config::AUTO_DISARM_MS)) {
      disarm();
    }

    // Firing State Machine
    switch (_fState) {
    case FiringState::IDLE:
      break;

    case FiringState::ESC_TEST:
      break;

    case FiringState::ARMING:
      if (now - _stateStartTime >= Config::ARM_DELAY_MS) {
        _isArmed = true;
        _fState = FiringState::IDLE;
        debugPrint(F("OK: SYSTEM ARMED"));
      }
      break;

    case FiringState::SPINNING_UP:
      if (now - _stateStartTime >= Config::SPINUP_MS) {
        _shot.attach(Config::PIN_SHOT);
        _shot.writeMicroseconds(shotNeutralUs + Config::SHOT_SPEED_OFFSET);
        _fState = FiringState::PUSHING;
        _stateStartTime = now;
      }
      break;

    case FiringState::PUSHING:
      if (now - _stateStartTime >= (uint32_t)shotDurationMs) {
        _shot.writeMicroseconds(shotNeutralUs - Config::BRAKE_OFFSET);
        _fState = FiringState::BRAKING;
        _stateStartTime = now;
      }
      break;

    case FiringState::BRAKING:
      if (now - _stateStartTime >= Config::BRAKE_MS) {
        _shot.writeMicroseconds(shotNeutralUs);
        applyFlywheelPower(0);

        _fState = FiringState::COOLDOWN;
        _stateStartTime = now;
      }
      break;

    case FiringState::COOLDOWN:
      if (now - _stateStartTime >= 100) {
        _shot.detach();
        _fState = FiringState::IDLE;
        debugPrint(F("OK: SHOT COMPLETE"));
      }
      break;
    }
  }
  int getShotZero() { return shotNeutralUs; }
  int getShotDur() { return shotDurationMs; }
};

#endif // LAUNCHER_H
