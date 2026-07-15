//
// Created by tozzi on 18.02.2026.
//

#include "FiringFSM.h"

// Konstruktor Implementierung
FiringFSM::FiringFSM(EscCallback onFlywheelPower,
                     ServoCallback onShotServo,
                     SimpleCallback onAttachESCs,
                     SimpleCallback onDetachESCs,
                     SimpleCallback onAttachShot,
                     SimpleCallback onDetachShot,
                     DebugCallback onDebug) :
    _currentState(FiringState::IDLE),
    _nextState(FiringState::IDLE),
    _stateStartTime(0),
    _lastActivityTime(0),
    _targetPower(0),
    _shotDuration(Config::SHOT_DURATION_DEFAULT),
    _shotNeutral(Config::SHOT_NEUTRAL_DEFAULT),
    _isArmed(false),
    _onFlywheelPower(onFlywheelPower),
    _onShotServo(onShotServo),
    _onAttachESCs(onAttachESCs),
    _onDetachESCs(onDetachESCs),
    _onAttachShot(onAttachShot),
    _onDetachShot(onDetachShot),
    _onDebug(onDebug) {}

/**
 * @brief Prüft Bedingungen, um in den nächsten Zustand zu wechseln.
 *
 * Beinhaltet Zeitprüfungen für Sequenzen (z.B. ARMING -> ARMED) sowie
 * Sicherheits-Timeouts (z.B. automatisches Disarm bei Inaktivität).
 */
void FiringFSM::evalTransition() {
    uint32_t now = millis();  // millis() aus der Arduino-Bibliothek: Gibt die Zeit in Millisekunden
    // seit Systemstart zurück

    // Nur wenn nicht bereits durch externe Befehle (z.B. Serial) ein Statuswechsel
    // angefordert wurde, evaluieren wir die internen (zeit-basierten) Timer:
    // Guard: trigger*()-Methoden setzen _nextState direkt.
    // evalTransition() darf das NICHT überschreiben.
    if (_nextState != _currentState) return;

    // State-spezifische Transitions (nur zeit-basiert)
    switch (_currentState) {
        case FiringState::IDLE:
            // Kein automatischer Übergang — nur via triggerArming()
            break;

        case FiringState::ARMING:
            // Kein Timer: Übergang sofort im nächsten Zyklus.
            // Die Verzögerung ist entry-Aktion in evalState() via delay().
            _nextState = FiringState::ARMED;
            break;

        case FiringState::ARMED:
            // Auto-Disarm nach Inaktivität
            if (now - _lastActivityTime >= Config::AUTO_DISARM_MS) {
                _nextState = FiringState::DISARMING;
            }
            break;

        case FiringState::DISARMING:
            // Nach dem Lösen der Motoren ist das System sicher (DISARMED).
            _nextState = FiringState::DISARMED;
            break;

        case FiringState::SPINNING_UP:
            // Quick SPINUP-Phase
            if (now - _stateStartTime >= Config::SPINUP_MS) {
                _nextState = FiringState::PUSHING;
            }
            break;

        case FiringState::PUSHING:
            // Nach shotDuration direkt in COOLDOWN — BRAKING ist ein extra Trigger.
            if (now - _stateStartTime >= (uint32_t)_shotDuration) {
                _nextState = FiringState::COOLDOWN;
            }
            break;

        case FiringState::BRAKING:
            // BRAKING wird via triggerBraking() betreten, Timer läuft danach normal.
            if (now - _stateStartTime >= Config::BRAKE_MS) {
                _nextState = FiringState::COOLDOWN;
            }
            break;
        case FiringState::COOLDOWN:
            // Schusssequenz beendet, System ist wieder bereit für den nächsten Schuss (ARMED).
            if (now - _stateStartTime >= Config::COOLDOWN_TIME) {
                _nextState = FiringState::ARMED;
            }
            break;

        default:
            break;
    }
}

/**
 * @brief Führt Eingangsaktionen (Entry) und kontinuierliche Aktionen aus.
 *
 * Behandelt das Ansteuern der Motoren und Servos sowie das
 * Senden von Debug-Status-Updates bei einem Zustandswechsel.
 */
void FiringFSM::evalState() {
    // State-Wechsel?
    if (_nextState != _currentState) {
        FiringState oldState = _currentState;
        {
            char dbg[48];
            snprintf(dbg, sizeof(dbg), "DBG evalState: %d -> %d", (int)oldState, (int)_nextState);
            _onDebug(dbg);
        }
        _currentState = _nextState;
        _stateStartTime = millis();

        // === Aktionen, die EINMALIG beim Eintritt in einen Zustand ausgeführt werden ===
        switch (_currentState) {
            case FiringState::IDLE:
                // IDLE start case
                // if (oldState == FiringState::COOLDOWN) {
                //     _onDetachShot();
                //     _onDebug("OK: SHOT COMPLETE");
                // }
                break;

            case FiringState::ARMING:
                _onDebug("STATUS: ARMING...");
                delay(Config::ARM_DELAY_MS);
                break;

            case FiringState::ARMED:
                _onAttachESCs();
                _isArmed = true;
                if (oldState == FiringState::COOLDOWN) {
                    _onDetachShot();
                    _onDebug("OK: SHOT COMPLETE");
                }
                _onDebug("OK: SYSTEM ARMED");
                break;

            case FiringState::DISARMING:
                // entry / isArmed=false, debug. Hardware-Trennung erst in DISARMED.
                _isArmed = false;
                _onDebug("STATUS: DISARMING sequence started...");
                break;

            case FiringState::DISARMED:
                // entry / ESCs und Servo hardwareseitig trennen
                _onDetachESCs();
                _onDetachShot();
                _onDebug("OK: SYSTEM IS DISARMED");
                break;

            case FiringState::SPINNING_UP:
                // entry / Schwungräder auf Zielleistung bringen
                _onFlywheelPower(_targetPower);
                _onDebug("STATUS: Spinning up...");
                break;

            case FiringState::PUSHING:
                // Den Servo wieder anmelden und in die Feuer-Position (nach vorne) ausfahren lassen
                _onAttachShot();
                _onShotServo(_shotNeutral + Config::SHOT_SPEED_OFFSET);
                break;

            case FiringState::BRAKING:
                // Den Servo in die Brems-/Rückzieh-Position (nach hinten) fahren lassen
                _onShotServo(_shotNeutral - Config::BRAKE_OFFSET);
                break;

            case FiringState::COOLDOWN:
                // Servoposition mittig ausrichten und Schwungräder stoppen
                _onShotServo(_shotNeutral);
                _onFlywheelPower(0);
                break;

            case FiringState::ESC_TEST:
                _onFlywheelPower(_targetPower);
                {
                    char buf[64];
                    snprintf(buf, sizeof(buf), "OK: Flywheels spinning at %d%%. Send STOP to end.", _targetPower);
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
 * @brief Auslöser: Startet die ARMEDschalt-Sequenz (Arming).
 */
void FiringFSM::triggerArming() {
    _lastActivityTime = millis();
    if (_isArmed || _currentState == FiringState::ARMING) return;
    if (_currentState == FiringState::IDLE || _currentState == FiringState::DISARMED) {
        _nextState = FiringState::ARMING;
        _stateStartTime = millis();
    }
}

/**
 * @brief Auslöser: Sofortiges Entschärfen (Not-Stopp / Safety Stop).
 */
void FiringFSM::triggerBraking() {
    if (_currentState != FiringState::PUSHING) {
        _onDebug("ERR: triggerBraking() nur aus PUSHING erlaubt!");
        return;
    }
    _nextState = FiringState::BRAKING;
    _stateStartTime = millis();
}

void FiringFSM::triggerDisarming() {
    if (_currentState == FiringState::CALIBRATING) {
        // Sonderfall verlässt evalState() und muss die DISARMED-Entry-Aktionen
        // (Hardware trennen, isArmed zurücksetzen) hier selbst nachholen.
        _onDetachESCs();
        _onDetachShot();
        _isArmed = false;
        _currentState = FiringState::IDLE;
        _nextState = FiringState::IDLE;
        _onDebug("OK: CALIBRATION FINISH (Sent MIN). Verify ESC beeps.");
        return;
    }
    _nextState = FiringState::DISARMING;
    _stateStartTime = millis();
}

/**
 * @brief Auslöser: Feuert einen einzelnen Dart ab.
 *
 * Funktioniert nur im Zustand ARMED. Startet die Schusssequenz:
 * SPINUP -> PUSH -> BRAKE -> COOLDOWN -> ARMED
 *
 * @param power Leistung der Schwungräder in Prozent (0-100).
 */
void FiringFSM::triggerFire(int power) {
    if (!_isArmed) {
        _onDebug("ERR: Arm first!");  // Nur schiessen, wenn das System auf ARMED steht.
        return;
    }  // Block shoting without arming first.
    // _isArmed ist nur wahr, wenn _currentState != IDLE (siehe ARMED/DISARMING-Entry-Aktionen),
    // daher ist die IDLE-Prüfung hier unerreichbar und entfällt.
    if (_currentState != FiringState::ARMED) return;
    _targetPower = power;
    _nextState = FiringState::SPINNING_UP;
    _stateStartTime = millis();
    recordActivity();  // Inaktivitäts-Timer zurücksetzen
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

void FiringFSM::recordActivity() {
    _lastActivityTime = millis();
}
void FiringFSM::setShotDuration(int ms) {
    _shotDuration = ms;
}
void FiringFSM::setShotNeutral(int us) {
    _shotNeutral = us;
}
FiringState FiringFSM::getCurrentState() const {
    return _currentState;
}
bool FiringFSM::isArmed() const {
    return _isArmed;
}

bool FiringFSM::canFire() const {
    return _isArmed && (_currentState == FiringState::ARMED || _currentState == FiringState::IDLE);
}

int FiringFSM::getShotDuration() const {
    return _shotDuration;
}
int FiringFSM::getShotNeutral() const {
    return _shotNeutral;
}