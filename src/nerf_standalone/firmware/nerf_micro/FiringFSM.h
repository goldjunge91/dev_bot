#ifndef FIRING_FSM_H
#define FIRING_FSM_H

#include "Config.h"
#include <Arduino.h>

enum class FiringState {
  IDLE,
  ARMING,
  ARMED,
  DISARMING,
  DISARMED,
  SPINNING_UP,
  PUSHING,
  BRAKING,
  COOLDOWN,
  ESC_TEST,
  CALIBRATING
};

// Callback-Typen (Function Pointers)
typedef void (*EscCallback)(int powerPercent);
typedef void (*ServoCallback)(int microseconds);
typedef void (*SimpleCallback)();
typedef void (*DebugCallback)(const char *msg);

class FiringFSM {
private:
  FiringState _currentState;
  FiringState _nextState;

  uint32_t _stateStartTime;
  uint32_t _lastActivityTime;

  // Transition-Parameter
  int _targetPower;
  int _shotDuration;
  int _shotNeutral;
  bool _isArmed;

  // Hardware-Callbacks
  EscCallback _onFlywheelPower;
  ServoCallback _onShotServo;
  SimpleCallback _onAttachESCs;
  SimpleCallback _onDetachESCs;
  SimpleCallback _onAttachShot;
  SimpleCallback _onDetachShot;
  DebugCallback _onDebug;

public:
  // Konstruktor mit Callbacks
  FiringFSM(EscCallback onFlywheelPower, ServoCallback onShotServo,
            SimpleCallback onAttachESCs, SimpleCallback onDetachESCs,
            SimpleCallback onAttachShot, SimpleCallback onDetachShot,
            DebugCallback onDebug)
      : _currentState(FiringState::IDLE), _nextState(FiringState::IDLE),
        _stateStartTime(0), _lastActivityTime(0), _targetPower(0),
        _shotDuration(Config::SHOT_DURATION_DEFAULT),
        _shotNeutral(Config::SHOT_NEUTRAL_DEFAULT), _isArmed(false),
        _onFlywheelPower(onFlywheelPower), _onShotServo(onShotServo),
        _onAttachESCs(onAttachESCs), _onDetachESCs(onDetachESCs),
        _onAttachShot(onAttachShot), _onDetachShot(onDetachShot),
        _onDebug(onDebug) {}

  // FSM Kern-Methoden (wie in Vorlesung)
  void evalTransition() {
    uint32_t now = millis();
    _nextState = _currentState; // Default: kein Wechsel

    // Auto-Disarm Check
    if (_isArmed &&
        (_currentState == FiringState::ARMED ||
         _currentState == FiringState::IDLE) &&
        (now - _lastActivityTime > Config::AUTO_DISARM_MS)) {
      _nextState = FiringState::DISARMING;
      return;
    }

    // State-spezifische Transitions
    switch (_currentState) {
    case FiringState::ARMING:
      if (now - _stateStartTime >= Config::ARM_DELAY_MS) {
        _nextState = FiringState::ARMED;
      }
      break;

    case FiringState::DISARMING:
      _nextState = FiringState::DISARMED;
      break;

    case FiringState::SPINNING_UP:
      if (now - _stateStartTime >= Config::SPINUP_MS) {
        _nextState = FiringState::PUSHING;
      }
      break;

    case FiringState::PUSHING:
      if (now - _stateStartTime >= (uint32_t)_shotDuration) {
        _nextState = FiringState::BRAKING;
      }
      break;

    case FiringState::BRAKING:
      if (now - _stateStartTime >= Config::BRAKE_MS) {
        _nextState = FiringState::COOLDOWN;
      }
      break;

    case FiringState::COOLDOWN:
      if (now - _stateStartTime >= 100) {
        _nextState = FiringState::ARMED;
      }
      break;

    default:
      break;
    }
  }

  void evalState() {
    // State-Wechsel?
    if (_nextState != _currentState) {
      FiringState oldState = _currentState;
      _currentState = _nextState;
      _stateStartTime = millis();

      // Entry-Aktionen
      switch (_currentState) {
      case FiringState::ARMING:
        _onAttachESCs();
        _onDebug("STATUS: ARMING sequence started (2s)...");
        break;

      case FiringState::ARMED:
        _isArmed = true;
        _onDebug("OK: SYSTEM ARMED");
        break;

      case FiringState::DISARMING:
        _isArmed = false;
        _onDebug("STATUS: DISARMING sequence started...");
        break;

      case FiringState::DISARMED:
        _onDetachESCs();
        _onDetachShot();
        _onDebug("OK: SYSTEM DISARMED (Signal Cut)");
        break;

      case FiringState::SPINNING_UP:
        _onFlywheelPower(_targetPower);
        _onDebug("STATUS: Spinning up...");
        break;

      case FiringState::PUSHING:
        _onAttachShot();
        _onShotServo(_shotNeutral + Config::SHOT_SPEED_OFFSET);
        break;

      case FiringState::BRAKING:
        _onShotServo(_shotNeutral - Config::BRAKE_OFFSET);
        break;

      case FiringState::COOLDOWN:
        _onShotServo(_shotNeutral);
        _onFlywheelPower(0);
        break;

      case FiringState::IDLE:
        if (oldState == FiringState::COOLDOWN) {
          _onDetachShot();
          _onDebug("OK: SHOT COMPLETE");
        }
        break;

      case FiringState::ESC_TEST:
        _onFlywheelPower(_targetPower);
        {
          char buf[64];
          sprintf(buf, "OK: Flywheels spinning at %d%%. Send STOP to end.",
                  _targetPower);
          _onDebug(buf);
        }
        break;

      case FiringState::CALIBRATING:
        // Handled by special case in triggerCalibration
        break;

      default:
        break;
      }
    }
  }

  // Events von außen (Bedingungen)
  void triggerArming() {
    _lastActivityTime = millis();
    if (_isArmed || _currentState == FiringState::ARMING)
      return;
    _nextState = FiringState::ARMING;
    _stateStartTime = millis();
  }

  void triggerDisarming() {
    // Special Case: Calibration finishing
    if (_currentState == FiringState::CALIBRATING) {
      _currentState = FiringState::IDLE;
      _nextState = FiringState::IDLE;
      _onDebug("OK: CALIBRATION FINISH (Sent MIN). Verify ESC beeps.");
      return;
    }
    _nextState = FiringState::DISARMING;
    _stateStartTime = millis();
  }

  void triggerFire(int power) {
    if (!_isArmed) {
      _onDebug("ERR: Arm first!");
      return;
    }
    if (_currentState != FiringState::ARMED &&
        _currentState != FiringState::IDLE)
      return;

    _targetPower = power;
    _nextState = FiringState::SPINNING_UP;
    _stateStartTime = millis();
    recordActivity();
  }

  void triggerCalibration() {
    if (!_isArmed) {
      _onDebug("ERR: Arm first!");
      return;
    }
    _onAttachESCs();
    _currentState = FiringState::CALIBRATING;
    _nextState = FiringState::CALIBRATING;
    _onDebug("WARNING: CALIBRATION MODE - MAX THROTTLE (2000us)");
    _onDebug("1. Connect Battery NOW (Wait for Beep-Beep)");
    _onDebug("2. Type 'STOP' immediately after beeps to finish");
  }

  void triggerEscTest(int power) {
    if (!_isArmed) {
      _onDebug("ERR: Arm first!");
      return;
    }
    _targetPower = power;
    _nextState = FiringState::ESC_TEST;
    _stateStartTime = millis();
    _lastActivityTime = millis();
  }

  void recordActivity() { _lastActivityTime = millis(); }

  // Setter
  void setShotDuration(int ms) { _shotDuration = ms; }
  void setShotNeutral(int us) { _shotNeutral = us; }

  // Getter
  FiringState getCurrentState() const { return _currentState; }
  bool isArmed() const { return _isArmed; }
  bool canFire() const {
    return _isArmed && (_currentState == FiringState::ARMED ||
                        _currentState == FiringState::IDLE);
  }
  int getShotDuration() const { return _shotDuration; }
  int getShotNeutral() const { return _shotNeutral; }
};

#endif // FIRING_FSM_H
