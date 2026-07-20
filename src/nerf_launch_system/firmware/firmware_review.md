# Code Review Bericht: Nerf Micro Firmware

Hier ist die detaillierte Auswertung der Firmware unter `src/nerf_launch_system/firmware/nerf_micro`. Der Code ist strukturiert und nutzt eine gute Aufteilung (FSM, Launcher, Comms), aber es gibt einige gravierende Logikfehler, Hardware-Risiken und Stellen, an denen der Code zu komplex oder redundant ist.

## 1. Logikfehler & Bugs (Kritisch)

### a) `millis()` Rollover Overflow (Timing Bug)

**Wo:**

- `lib/Control/Launcher.cpp` (Zeilen 35, 38, 42, 50, 54, 152, 177, 191)
- `lib/Control/TiltController.cpp` (Zeilen 18, 47)

**Code:**

```cpp
// Launcher.cpp (Zeile 152)
_manualTimer = millis() + duration;  // non-blocking sequence start

// Launcher.cpp (Zeile 35)
if (_manualState != ManualState::IDLE && now >= _manualTimer) {
```

**Problem:** Wenn `millis()` nach ca. 49 Tagen überläuft (Overflow), wird die Bedingung `now >= _manualTimer` sofort wahr und das Timing bricht unvorhersehbares ab.
**Lösung:** Zeitdifferenzen *immer* durch Subtraktion berechnen: `if (now - startTime >= duration)`.

### b) Servo-Überhitzung in `TiltController::setPosition`

**Wo:** `lib/Control/TiltController.cpp` (Zeilen 74-78)

**Code:**

```cpp
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    _tiltServo.writeMicroseconds(us);
    // reset moving state so update() doesn't detach immediately
    _state = State::IDLE;
```

**Problem:** In `setPosition(int us)` wird der Move ausgeführt und am Ende explizit `_state = State::IDLE;` gesetzt. Die `update()` Methode hängt den Servo (via `detach()`) aber *nur* ab, wenn der State von `MOVING` auf `IDLE` springt. Durch das direkte Setzen auf `IDLE` wird der Servo dauerhaft bestromt, was zu Überhitzung oder "Zittern" führen kann, was das Design eigentlich verhindern sollte.

### c) Zustandsautomaten-Bypass in `FiringFSM::triggerDisarming`

**Wo:** `lib/FSM/FiringFSM.cpp` (Zeilen 225-228)

**Code:**

```cpp
void FiringFSM::triggerDisarming() {
    if (_currentState == FiringState::CALIBRATING) {
        _currentState = FiringState::IDLE;
        _nextState = FiringState::IDLE;
        // ...
```

**Problem:** Die FSM-Variablen werden direkt überschrieben. Dadurch wird die zentrale Logik in `evalState()` umgangen. Wichtige "Exit"-Aktionen (wie z.B. Motoren Hardware-seitig via `_onDetachESCs()` anhalten) werden umgangen, was Sicherheitsrisiken birgt.

## 2. Redundanter & Überflüssiger Code

### a) Doppelter Schuss-Zyklus (`Launcher::update` vs. `FiringFSM`)

**Wo:** `lib/Control/Launcher.cpp` (Zeilen 36-64)

**Code:**

```cpp
// Auszug Launcher.cpp (Zeilen 36-40)
        if (_manualState == ManualState::TEST_SHOT_PUSH) {
            _shot.writeMicroseconds(_fsm.getShotNeutral() - Config::BRAKE_OFFSET);
            _manualTimer = now + Config::BRAKE_MS;
            _manualState = ManualState::TEST_SHOT_BRAKE;
// [...] kopiert im Grunde komplett die Logik aus FiringFSM::evalState
```

**Problem:** Die FSM steuert den Servo professionell (PUSHING -> BRAKING -> COOLDOWN). In `Launcher::update()` wurde für `TEST_SHOT` und `DANGEROUS_SHOT` jedoch eine komplett eigene manuelle State-Machine (`ManualState`) nachgebaut, die denselben Ablauf abbildet. Dies bläht den Code auf und führt zu Hardware-Konflikten.

### b) Redundante Bedingung in `FiringFSM::triggerFire`

**Wo:** `lib/FSM/FiringFSM.cpp` (Zeile 248)

**Code:**

```cpp
    if (!_isArmed) {
        _onDebug("ERR: Arm first!");
        return;
    } // ...
    if (_currentState != FiringState::ARMED && _currentState != FiringState::IDLE) return;
```

**Problem:** Da `_isArmed` ohnehin auf `false` steht, wenn das System im Zustand `IDLE` ist, bricht der Code immer schon in der ersten Zeile ab. Die Prüfung auf `_currentState != FiringState::IDLE` in Zeile 248 kann gar nicht mehr erreicht werden und ist tot.

### c) Veraltete Comms-Befehle

**Wo:** `lib/Comms/Comms.cpp` (Zeilen 118-121)

**Code:**

```cpp
    // Calibration & Test shortcuts handled via FSM now
    else if (cmd == "CAL_MAX" || cmd == "CAL_MIN" || cmd == "CAL_TEST") {
        broadcast(F("ERR: Obsolete commands. Use 'CAL' state via FSM instead."));
    }
```

**Problem:** Diese Befehle existieren nicht mehr und verschwenden in Form dieser Strings kostbaren Programmspeicher.

## 3. Code-Qualität & Komplexität

### a) Fragmentierung des Speichers durch `String` Klasse

**Wo:** `lib/Comms/Comms.cpp` (Zeilen 45-58 und 74-92)

**Code:**

```cpp
// Comms.cpp Zeile 55
        else if (c >= 32 && c <= 126) {
            _buffer += c;
        }

// Comms.cpp Zeile 90-92
    int spaceIdx = line.indexOf(' ');
    String cmd = (spaceIdx == -1) ? line : line.substring(0, spaceIdx);
    String argStr = (spaceIdx == -1) ? "" : line.substring(spaceIdx + 1);
```

**Problem:** Auf AVR-Mikrocontrollern ohne Speichermanagement führt die ständige dynamische Reallokation der `String`-Klasse (`_buffer += c` oder `.substring`) zur **Heap-Fragmentierung** und unweigerlich zu unvorhersehbaren Laufzeit-Abstürzen. Man sollte besser C-Strings (z.B. `char _buffer[32]`) und `strcmp` verwenden.

### b) Static Callback Workarounds in `Launcher.cpp`

**Wo:** `lib/Control/Launcher.cpp` (Zeilen 7, 107-132)

**Code:**

```cpp
// Zeile 7
Launcher *Launcher::_instance = nullptr;

// Zeilen 111-113
void Launcher::callbackESCPower(int pwr) {
    _instance->setESCPower(pwr);
}
```

**Problem:** Die `FiringFSM` erwartet C-Funktionszeiger. Da C++ es nicht erlaubt, Klassen-Methoden direkt als normale Funktionspointer zu übergeben, wurde in `Launcher.cpp` ein unschöner Workaround mit einer statischen Singleton-Referenz (`_instance`) gebaut. Abstrakte Interface-Klassen (z.B. `class IHardwareInfo { virtual void attachEsc() = 0; }`) wären hier eine deutlich sauberere Lösung.
