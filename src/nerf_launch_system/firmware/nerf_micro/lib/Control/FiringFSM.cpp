//
// Created by tozzi on 18.02.2026.
//

#include "FiringFSM.h"

// Konstruktor Implementierung
FiringFSM::FiringFSM(
  EscCallback onFlywheelPower,
  ServoCallback onShotServo,
  SimpleCallback onAttachESCs,
  SimpleCallback onDetachESCs,
  SimpleCallback onAttachShot,
  SimpleCallback onDetachShot,
  DebugCallback onDebug)
: _currentState(FiringState::IDLE),
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
void FiringFSM::evalTransition()
{
  uint32_t now = millis();    // millis() aus der Arduino-Bibliothek: Gibt die Zeit in Millisekunden
                              // seit Systemstart zurück

  // Nur wenn nicht bereits durch externe Befehle (z.B. Serial) ein Statuswechsel
  // angefordert wurde, evaluieren wir die internen (zeit-basierten) Timer:
  if (_nextState == _currentState) {
    // === 1. Automatisches Entschärfen (Auto-Disarm) ===
    // Wenn das System scharf (ARMED) oder im Leerlauf (IDLE) ist, aber zu lange
    // nichts passiert (= Inaktivität), wird es aus Sicherheitsgründen entschärft.
    if (_isArmed &&
      (_currentState == FiringState::ARMED || _currentState == FiringState::IDLE) &&
      (now - _lastActivityTime > Config::AUTO_DISARM_MS))
    {
      _nextState = FiringState::DISARMING;
      return;
    }

    // State-spezifische Transitions
    switch (_currentState) {
      case FiringState::ARMING:
        // Nach Ablauf der Sicherheitsverzögerung wird das System SCHARF geschaltet.
        if (now - _stateStartTime >= Config::ARM_DELAY_MS) {
          _nextState = FiringState::ARMED;
        }
        break;

      case FiringState::DISARMING:
        // Nach dem Lösen der Motoren ist das System sicher (DISARMED).
        _nextState = FiringState::DISARMED;
        break;

      case FiringState::SPINNING_UP:
        // Motoren haben lange genug beschleunigt, jetzt Dart in die Räder schieben
        // (PUSHING).
        if (now - _stateStartTime >= Config::SPINUP_MS) {
          _nextState = FiringState::PUSHING;
        }
        break;

      case FiringState::PUSHING:
        // Pusher-Servo macht eine volle 360 grad umdrehung
        // (BRAKING).
        if (now - _stateStartTime >= (uint32_t)_shotDuration) {
          _nextState = FiringState::BRAKING;
        }
        break;

      case FiringState::BRAKING:
        // Pusher ist auf home pisition, kurze Pause zur Abkühlung (COOLDOWN).
        if (now - _stateStartTime >= Config::BRAKE_MS) {
          _nextState = FiringState::COOLDOWN;
        }
        break;

      case FiringState::COOLDOWN:
        // Schusssequenz beendet, System ist wieder bereit für den nächsten Schuss (ARMED).
        if (now - _stateStartTime >= 100) {
          _nextState = FiringState::ARMED;
        }
        break;

      case FiringState::IDLE:
      case FiringState::ARMED:
      case FiringState::DISARMED:
      case FiringState::ESC_TEST:
      case FiringState::CALIBRATING:
        // Diese Zustände erfordern im regulären Betrieb keine automatischen
        // zeitgesteuerten Übergänge. Übergänge werden durch externe Events ausgelöst.
        break;

      default:
        break;
    }
  }
}

/**
 * @brief Wendet den Zustandswechsel an und führt Entry/Exit-Aktionen aus.
 *
 * Wird nur aktiv, wenn `_nextState != _currentState`. Führt dann GENAU EINMAL
 * die Hardware-Aktionen (Schwungräder/Servos) für den neuen Zustand aus.
 * Es gibt hier keine kontinuierlichen Aktionen.
 */
void FiringFSM::evalState()
{
  // State-Wechsel?
  if (_nextState != _currentState) {
    FiringState oldState = _currentState;
    {
      char dbg[48];
      snprintf(
        dbg, sizeof(dbg), "DBG evalState: %d -> %d", static_cast<int>(oldState),
        static_cast<int>(_nextState));                                                                                  // NOLINT
      _onDebug(dbg);
    }
    _currentState = _nextState;
    _stateStartTime = millis();

    // === Aktionen, die EINMALIG beim Eintritt in einen Zustand ausgeführt werden ===
    switch (_currentState) {
      case FiringState::ARMING:
        // ESCs am Arduino "anmelden" und 2 Sekunden warten, um plötzlichen Start zu
        // verhindern
        _onAttachESCs();
        _onDebug("STATUS: ARMING sequence started (2s)...");
        break;

      case FiringState::ARMED:
        // System ist nun feuereit
        _isArmed = true;
        _onDebug("OK: SYSTEM ARMED");
        break;

      case FiringState::DISARMING:
        _isArmed = false;
        _onDebug("STATUS: DISARMING sequence started...");
        break;

      case FiringState::DISARMED:
        // Aus Sicherheitsgründen wird die Verbindung zu ESCs und Pusher-Servo
        // hardwareseitig getrennt
        _onDetachESCs();
        _onDetachShot();
        _onDebug("OK: SYSTEM DISARMED (Signal Cut)");
        break;

      case FiringState::SPINNING_UP:
        // Den Motoren den Befehl geben, Gas zu geben (%-Wert)
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

      case FiringState::IDLE:
        // Wenn wir aus dem Cooldown (nach einem Schuss) kommen, können wir den Servo sicher
        // trennen
        if (oldState == FiringState::COOLDOWN) {
          _onDetachShot();
          _onDebug("OK: SHOT COMPLETE");
        }
        break;

      case FiringState::ESC_TEST:
        _onFlywheelPower(_targetPower);
        {
          char buf[64];
          snprintf(
            buf, sizeof(buf), "OK: Flywheels spinning at %d%%. Send STOP to end.",
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
 * @brief Auslöser: Startet die Scharfschalt-Sequenz (Arming).
 */
void FiringFSM::triggerArming()
{
  _lastActivityTime = millis();
  if (_isArmed || _currentState == FiringState::ARMING) {return;}
  _nextState = FiringState::ARMING;
  _stateStartTime = millis();
}

/**
 * @brief Auslöser: Sofortiges Entschärfen (Not-Stopp / Safety Stop).
 */
void FiringFSM::triggerDisarming()
{
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
 * @brief Auslöser: Feuert einen einzelnen Dart ab.
 *
 * Funktioniert nur im Zustand ARMED. Startet die Schusssequenz:
 * SPINUP -> PUSH -> BRAKE -> COOLDOWN -> ARMED
 *
 * @param power Leistung der Schwungräder in Prozent (0-100).
 */
void FiringFSM::triggerFire(int power)
{
  if (!_isArmed) {
    _onDebug("ERR: Arm first!");      // Nur schiessen, wenn das System auf ARMED steht.
    return;
  }
  // Verhindert, dass wir einen Schuss starten, obwohl wir gerade schon schiessen (FSM blockiert)
  if (_currentState != FiringState::ARMED && _currentState != FiringState::IDLE) {return;}

  // Wechsel in die erste Phase der Schusssequenz
  _targetPower = power;
  _nextState = FiringState::SPINNING_UP;
  _stateStartTime = millis();
  recordActivity();    // Inaktivitäts-Timer zurücksetzen
}

void FiringFSM::triggerCalibration()
{
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

void FiringFSM::triggerEscTest(int power)
{
  if (!_isArmed) {
    _onDebug("ERR: Arm first!");
    return;
  }
  _targetPower = power;
  _nextState = FiringState::ESC_TEST;
  _stateStartTime = millis();
  _lastActivityTime = millis();
}

void FiringFSM::recordActivity()
{
  _lastActivityTime = millis();
}
void FiringFSM::setShotDuration(int ms)
{
  _shotDuration = ms;
}
void FiringFSM::setShotNeutral(int us)
{
  _shotNeutral = us;
}
FiringState FiringFSM::getCurrentState() const
{
  return _currentState;
}
bool FiringFSM::isArmed() const
{
  return _isArmed;
}

bool FiringFSM::canFire() const
{
  return _isArmed && (_currentState == FiringState::ARMED || _currentState == FiringState::IDLE);
}

int FiringFSM::getShotDuration() const
{
  return _shotDuration;
}
int FiringFSM::getShotNeutral() const
{
  return _shotNeutral;
}
