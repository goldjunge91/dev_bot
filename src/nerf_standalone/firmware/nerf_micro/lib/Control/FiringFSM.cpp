//
// Created by tozzi on 18.02.2026.
//

#include "FiringFSM.h"

// Konstruktor Implementierung
FiringFSM::FiringFSM(EscCallback onFlywheelPower, ServoCallback onShotServo,
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
      _onDebug(onDebug) {
}

/**
 * @brief Checks conditions to switch to the next state.
 *
 * Includes timing checks for sequences (ARMING -> ARMED) and
 * safety timeouts (Auto-Disarm).
 */
void FiringFSM::evalTransition() {
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
            if (now - _stateStartTime >= (uint32_t) _shotDuration) {
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

/**
 * @brief Performs Entry Actions and Continuous Actions for states.
 *
 * Handles keeping the flywheels spinning, moving servos, and sending
 * debug status updates when states change.
 */
void FiringFSM::evalState() {
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
                _onFlywheelPower(_targetPower); {
                    char buf[64];
                    sprintf(buf, "OK: Flywheels spinning at %d%%. Send STOP to end.",
                            _targetPower);
                    _onDebug(buf);
                }
                break;

            case FiringState::CALIBRATING:
                break;

            default:
                break;
        }
    }
}

/**
 * @brief Trigger: Start the Arming sequence.
 */
void FiringFSM::triggerArming() {
    _lastActivityTime = millis();
    if (_isArmed || _currentState == FiringState::ARMING)
        return;
    _nextState = FiringState::ARMING;
    _stateStartTime = millis();
}

/**
 * @brief Trigger: Disarm immediately (Safety Stop).
 */
void FiringFSM::triggerDisarming() {
    if (_currentState == FiringState::CALIBRATING) {
        _currentState = FiringState::IDLE;
        _nextState = FiringState::IDLE;
        _onDebug("OK: CALIBRATION FINISH (Sent MIN). Verify ESC beeps.");
        return;
    }
    _nextState = FiringState::DISARMING;
    _stateStartTime = millis();
}

/**
 * @brief Trigger: Fire a shot.
 *
 * Only works if ARMED. Starts the firing sequence:
 * SPINUP -> PUSH -> BRAKE -> COOLDOWN -> ARMED
 *
 * @param power Flywheel power percentage (0-100).
 */
void FiringFSM::triggerFire(int power) {
    if (!_isArmed) {
        _onDebug("ERR: Arm first!");
        return;
    }
    if (_currentState != FiringState::ARMED && _currentState != FiringState::IDLE)
        return;

    _targetPower = power;
    _nextState = FiringState::SPINNING_UP;
    _stateStartTime = millis();
    recordActivity();
}

void FiringFSM::triggerCalibration() {
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

void FiringFSM::triggerEscTest(int power) {
    if (!_isArmed) {
        _onDebug("ERR: Arm first!");
        return;
    }
    _targetPower = power;
    _nextState = FiringState::ESC_TEST;
    _stateStartTime = millis();
    _lastActivityTime = millis();
}

void FiringFSM::recordActivity() { _lastActivityTime = millis(); }
void FiringFSM::setShotDuration(int ms) { _shotDuration = ms; }
void FiringFSM::setShotNeutral(int us) { _shotNeutral = us; }
FiringState FiringFSM::getCurrentState() const { return _currentState; }
bool FiringFSM::isArmed() const { return _isArmed; }

bool FiringFSM::canFire() const {
    return _isArmed && (_currentState == FiringState::ARMED ||
                        _currentState == FiringState::IDLE);
}

int FiringFSM::getShotDuration() const { return _shotDuration; }
int FiringFSM::getShotNeutral() const { return _shotNeutral; }