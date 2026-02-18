#ifndef LAUNCHER_H
#define LAUNCHER_H

#include "Config.h"
#include "FiringFSM.h"
#include <Arduino.h>
#include <Servo.h>

class Launcher {
private:
  Servo _escLeft, _escRight, _shot;

  // Static instance pointer for callbacks
  static Launcher *_instance;

  // FSM Member
  FiringFSM _fsm;

  // Hardware action methods (called by FSM via callbacks)
  void setESCPower(int powerPercent) {
    int powerLimit = constrain(powerPercent, 0, 100);
    // Standard ESCs: 0% = ESC_MIN (1000us), 100% = ESC_MAX (2000us)
    int us = map(powerLimit, 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(us);
    _escRight.writeMicroseconds(us);
  }

  void setShotServo(int us) { _shot.writeMicroseconds(us); }

  void attachESCs() {
    _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_ARM);
    _escRight.writeMicroseconds(Config::ESC_ARM);
  }

  void detachESCs() {
    if (_escLeft.attached())
      _escLeft.detach();
    if (_escRight.attached())
      _escRight.detach();
  }

  void attachShotServo() {
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
  }

  void detachShotServo() { _shot.detach(); }

  static void debugOutput(const char *msg) {
    Serial.println(msg);
    Serial1.println(msg);
  }

  // Static callback wrappers (C++ member → C function pointer)
  static void callbackESCPower(int pwr) { _instance->setESCPower(pwr); }

  static void callbackShotServo(int us) { _instance->setShotServo(us); }

  static void callbackAttachESCs() { _instance->attachESCs(); }

  static void callbackDetachESCs() { _instance->detachESCs(); }

  static void callbackAttachShot() { _instance->attachShotServo(); }

  static void callbackDetachShot() { _instance->detachShotServo(); }

  static void callbackDebug(const char *msg) { debugOutput(msg); }

public:
  // Constructor - Initialize FSM with callbacks
  Launcher()
      : _fsm(callbackESCPower, callbackShotServo, callbackAttachESCs,
             callbackDetachESCs, callbackAttachShot, callbackDetachShot,
             callbackDebug) {
    _instance = this;
  }

  void begin() {
    // SAFETY: Ensure everything is detached on boot
    if (_escLeft.attached())
      _escLeft.detach();
    if (_escRight.attached())
      _escRight.detach();
    _shot.detach();
  }

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

  // --- FSM EVENT TRIGGERS ---
  void arming() { _fsm.triggerArming(); }

  void disarming() { _fsm.triggerDisarming(); }

  void startFire(int pwr) { _fsm.triggerFire(pwr > 0 ? pwr : 40); }

  void testEsc(int pwr) { _fsm.triggerEscTest(pwr); }

  void startCalibration() { _fsm.triggerCalibration(); }

  void recordActivity() { _fsm.recordActivity(); }

  // --- MANUAL ACTIONS (NOT FSM-CONTROLLED) ---

  void testShot(int ms) {
    int duration = (ms > 0) ? ms : _fsm.getShotDuration();
    debugPrintf("OK: Test shot %d ms", duration);

    // Safety: Ensure flywheels are stopped for TEST_SHOT
    bool escWasAttached = _escLeft.attached() || _escRight.attached();
    if (_escLeft.attached() || _escRight.attached()) {
      setESCPower(0);
      delay(20);
      detachESCs();
    }
    if (escWasAttached) {
      debugPrint(F("WARN: ESCs were attached during TEST_SHOT; forced stop."));
    }

    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    _shot.writeMicroseconds(_fsm.getShotNeutral() + Config::TEST_SHOT_OFFSET);

    delay(duration);

    // Active Brake
    _shot.writeMicroseconds(_fsm.getShotNeutral() - Config::BRAKE_OFFSET);
    delay(Config::BRAKE_MS);
    _shot.writeMicroseconds(_fsm.getShotNeutral());
    delay(50);
    _shot.detach();
    recordActivity();
  }

  // --- CALIBRATION HELPERS (User Logic) ---
  void calibrateMax() {
    if (!_escLeft.attached())
      _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    if (!_escRight.attached())
      _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_MAX);
    _escRight.writeMicroseconds(Config::ESC_MAX);
    debugPrint(F("Sending maximum throttle"));
  }

  void calibrateMin() {
    if (!_escLeft.attached())
      _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    if (!_escRight.attached())
      _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_MIN);
    _escRight.writeMicroseconds(Config::ESC_MIN);
    debugPrint(F("Sending minimum throttle"));
  }

  void testSequence() {
    debugPrint(F("Running test in 3..."));
    delay(1000);
    debugPrint(F("Running test in 2..."));
    delay(1000);
    debugPrint(F("Running test in 1..."));
    delay(1000);

    // Ramp UP
    for (uint16_t i = Config::ESC_MIN; i <= Config::ESC_MAX; i += 5) {
      _escLeft.writeMicroseconds(i);
      _escRight.writeMicroseconds(i);
      debugPrintf("Pulse length = %d", i);
      delay(200);
    }

    debugPrint(F("STOP"));
    _escLeft.writeMicroseconds(Config::ESC_MIN);
    _escRight.writeMicroseconds(Config::ESC_MIN);
  }

  void nudge(bool forward) {
    debugPrint(F("STATUS: Nudging..."));
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    int s =
        forward ? (_fsm.getShotNeutral() + 500) : (_fsm.getShotNeutral() - 500);
    _shot.writeMicroseconds(s);
    delay(200);
    _shot.writeMicroseconds(_fsm.getShotNeutral());
    delay(50);
    _shot.detach();

    char buf[64];
    sprintf(buf, "OK: Nudge %s (Signal: %d)", forward ? "Fwd" : "Back", s);
    Serial.println(buf);
    Serial1.println(buf);

    recordActivity();
  }

  void setRawPWM(int us) {
    if (!_fsm.isArmed()) {
      debugPrint(F("ERR: Arm first!"));
      return;
    }
    if (!_escLeft.attached())
      _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    if (!_escRight.attached())
      _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(us);
    _escRight.writeMicroseconds(us);
    debugPrintf("OK: Manual PWM %d us", us);
  }

  // --- CONFIG SETTERS ---
  void setZS(int v) {
    _fsm.setShotNeutral(v);
    debugPrintf("OK: Shot Zero set to %d", v);
  }

  void setD(int v) {
    _fsm.setShotDuration(v);
    debugPrintf("OK: Duration set to %d", v);
  }

  void printConfig() {
    debugPrint(F("\n--- CURRENT CONFIG ---"));
    debugPrintf("Shot Zero:     %d us", _fsm.getShotNeutral());
    debugPrintf("Shot Duration: %d ms", _fsm.getShotDuration());
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

  // --- UPDATE LOOP ---
  void update() {
    _fsm.evalTransition(); // Prüft Bedingungen, setzt nextState
    _fsm.evalState();      // Führt State-Aktionen aus
  }

  // Getter
  bool isArmed() { return _fsm.isArmed(); }
  int getShotZero() { return _fsm.getShotNeutral(); }
  int getShotDur() { return _fsm.getShotDuration(); }
  FiringFSM &getFSM() { return _fsm; }
};

// Static member initialization
Launcher *Launcher::_instance = nullptr;

#endif // LAUNCHER_H
