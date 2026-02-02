/**
 * NERF OS PRO - Final Stable Version (TEST_SHOT FIXED)
 * Hardware: Arduino Pro Micro / Leonardo
 * Pins: D2/D3 (ESCs), D9 (Shot), D10 (Tilt)
 */

#include <Arduino.h>
#include <Servo.h>

namespace Config {
const uint8_t PIN_FLY_L = 2;
const uint8_t PIN_FLY_R = 3;
const uint8_t PIN_SHOT = 9;
const uint8_t PIN_TILT = 10;

// --- ESC DIRECTION & RANGE ---
// Falls ein Motor falsch herum dreht, hier auf 'true' setzen (erfordert
// Bidirectional ESCs) Falls du Standard-ESCs hast: Zwei der drei Motorkabel
// physisch tauschen!
const bool INV_L = false;
const bool INV_R = false;

const uint16_t ESC_MIN = 1000;
const uint16_t ESC_MAX = 2000;
const uint16_t ESC_ARM = 1000; // Stillstand (bei Standard ESCs)
const uint16_t ESC_MID = 1500; // Neutral (nur bei Bidirectional relevant)

// --- TIMINGS ---
const uint32_t ARM_DELAY_MS = 2000;
const uint32_t SPINUP_MS = 1200;
const uint32_t AUTO_DISARM_MS = 60000;

// Deine kalibrierten Werte
const uint16_t SHOT_NEUTRAL_DEFAULT = 1430;
const uint16_t TILT_NEUTRAL_DEFAULT = 1430;
const uint32_t SHOT_DURATION_DEFAULT = 2520;
const uint16_t SHOT_SPEED_OFFSET = 220;
// ZEIT: 2210ms | SPEED: 300 | NEUTRAL: 1430
// ZEIT: 2520ms | SPEED: 220 | NEUTRAL: 1430

// Brems-Parameter
const uint16_t BRAKE_OFFSET = 600;
const uint16_t BRAKE_MS = 15;

const uint32_t BAUD_RATE = 115200;
} // namespace Config

enum class FiringState {
  IDLE,
  ARMING,
  SPINNING_UP,
  PUSHING,
  BRAKING,
  COOLDOWN,
  ESC_TEST
};
enum class TiltState { TILT_IDLE, TILT_MOVING };

class Launcher {
private:
  Servo _escL, _escR, _shot;
  FiringState _fState = FiringState::IDLE;
  TiltState _tState = TiltState::TILT_IDLE;

  bool _isArmed = false;
  uint32_t _stateStartTime = 0;
  uint32_t _tiltEndTime = 0;
  uint32_t _lastActivityTime = 0;

  int shotNeutralUs = Config::SHOT_NEUTRAL_DEFAULT;
  int tiltNeutralUs = Config::TILT_NEUTRAL_DEFAULT;
  int shotDurationMs = Config::SHOT_DURATION_DEFAULT;

  // Zentrale Hilfsfunktion für synchronen Power-Output
  void applyFlywheelPower(int powerPercent) {
    int powerLimit = constrain(powerPercent, 0, 100);

    // Berechnung für Linken Motor
    int usL = Config::INV_L ? map(powerLimit, 0, 100, Config::ESC_MID,
                                  Config::ESC_MIN) // Rückwärts-Mapping
                            : map(powerLimit, 0, 100, Config::ESC_MIN,
                                  Config::ESC_MAX); // Vorwärts-Mapping

    // Berechnung für Rechten Motor
    int usR = Config::INV_R ? map(p, 0, 100, Config::ESC_MID, Config::ESC_MIN)
                            : map(p, 0, 100, Config::ESC_MIN, Config::ESC_MAX);

    _escL.writeMicroseconds(usL);
    _escR.writeMicroseconds(usR);
  }

public:
  void begin() {
    _lastActivityTime = millis();
    printHelp();
  }

  // --- HELPER OUTPUT (USB & UART) ---
  void debugPrint(const __FlashStringHelper *msg) {
    Serial.println(msg);
    Serial1.println(msg);
  }
  void debugPrint(const char *msg) {
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

  void arm() {
    if (_isArmed || _fState == FiringState::ARMING)
      return;
    _escL.attach(Config::PIN_FLY_L, Config::ESC_MIN, Config::ESC_MAX);
    _escR.attach(Config::PIN_FLY_R, Config::ESC_MIN, Config::ESC_MAX);
    _escL.writeMicroseconds(Config::ESC_ARM);
    _escR.writeMicroseconds(Config::ESC_ARM);
    // delay(2000);
    // _isArmed = true;
    // _lastActivityTime = millis();
    // debugPrint(F("OK: SYSTEM ARMED"));
    _fState = FiringState::ARMING;
    _stateStartTime = millis();
    _lastActivityTime = millis();
    debugPrint(F("STATUS: ARMING sequence started (2s)..."));
  }

  void disarm() {
    _isArmed = false;
    _fState = FiringState::IDLE;
    if (_escL.attached())
      _escL.writeMicroseconds(Config::ESC_ARM);
    if (_escR.attached())
      _escR.writeMicroseconds(Config::ESC_ARM);
    _shot.detach();
    _tilt.detach();
    debugPrint(F("OK: SYSTEM DISARMED"));
  }

  void testEsc(int pwr) {
    if (!_isArmed) {
      debugPrint(F("ERR: Arm first!"));
      return;
    }
    int us =
        map(constrain(pwr, 0, 100), 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    _escL.writeMicroseconds(us);
    _escR.writeMicroseconds(us);
    _fState = FiringState::ESC_TEST;
    debugPrintf("OK: Flywheels spinning at %d%%. Send STOP to end.", pwr);
    _lastActivityTime = millis();
  }

  void printConfig() {
    debugPrint(F("\n--- CURRENT CONFIG ---"));
    debugPrintf("Shot Zero:     %d us", shotNeutralUs);
    debugPrintf("Tilt Zero:     %d us", tiltNeutralUs);
    debugPrintf("Shot Duration: %d ms", shotDurationMs);
    debugPrint(F("----------------------"));
  }

  void printHelp() {
    debugPrint(F("\n--- COMMAND LIST ---"));
    debugPrint(F(" > ARM / DISARM      - Safety Control"));
    debugPrint(F(" > SHOT <pwr>        - Fire Sequence (0-80)"));
    debugPrint(F(" > NF / NB           - Nudge Shot Fwd/Back"));
    debugPrint(F(" > TEST_SHOT <ms>    - Test Pusher Only"));
    debugPrint(F(" > UP <ms> / DN <ms> - Tilt Move"));
    debugPrint(F(" > ZERO_S <us>       - Set Shot Neutral"));
    debugPrint(F(" > ZERO_T <us>       - Set Tilt Neutral"));
    debugPrint(F(" > SET_SHOT <ms>     - Set Shot Duration"));
    debugPrint(F(" > SAVE              - Show Config"));
    debugPrint(F("--------------------"));
  }

  void testShot(int ms) {
    int duration = (ms > 0) ? ms : shotDurationMs;
    debugPrintf("OK: Test shot %d ms", duration);
    _shot.attach(Config::PIN_SHOT);
    _shot.writeMicroseconds(shotNeutralUs + Config::SHOT_SPEED_OFFSET);
    delay(duration);
    // Aktive Bremse
    _shot.writeMicroseconds(shotNeutralUs - Config::BRAKE_OFFSET);
    delay(Config::BRAKE_MS);
    _shot.writeMicroseconds(shotNeutralUs);
    delay(50);
    _shot.detach();
    recordActivity();
  }

  void nudge(bool forward) {
    // Wir nutzen den vollen Pulsbereich für maximale Kompatibilität
    _shot.attach(Config::PIN_SHOT, 500, 2500);

    // Nutze deinen ermittelten Speed-Offset von 300 für genug Kraft
    int s = forward ? (shotNeutralUs + 300) : (shotNeutralUs - 300);

    _shot.writeMicroseconds(s);
    delay(100); // Von 40ms auf 100ms erhöht, damit der Motor Zeit zum Anlaufen
                // hat

    _shot.writeMicroseconds(shotNeutralUs);
    delay(50);
    _shot.detach();

    // Debug-Ausgabe zur Kontrolle im Monitor
    debugPrintf(forward ? "OK: Nudge Forward (Signal: %d)"
                        : "OK: Nudge Backward (Signal: %d)",
                s);
    _lastActivityTime = millis();
  }

  void recordActivity() { _lastActivityTime = millis(); }

  void startFire(int pwr) {
    if (!_isArmed) {
      debugPrint(F("ERR: Arm first!"));
      return;
    }
    if (_fState != FiringState::IDLE)
      return;

    int us =
        map(constrain(pwr, 0, 100), 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    _escL.writeMicroseconds(us);
    _escR.writeMicroseconds(us);

    _fState = FiringState::SPINNING_UP;
    _stateStartTime = millis();
    recordActivity();
    debugPrint(F("STATUS: Spinning up..."));
  }
  // Testet nur den Pusher ohne Flywheels (inkl. Bremse)
  void testShot(int ms) {
    int duration = (ms > 0) ? ms : shotDurationMs;
    shotServo.attach(Config::PIN_SHOT, 500, 2500);
    shotServo.writeMicroseconds(shotNeutralUs + Config::SHOT_SPEED_OFFSET);
    delay(duration);
    // Aktive Bremse
    shotServo.writeMicroseconds(shotNeutralUs - Config::BRAKE_OFFSET);
    delay(Config::BRAKE_MS);
    shotServo.writeMicroseconds(shotNeutralUs);
    delay(50);
    shotServo.detach();
    debugPrintf("OK: Test Shot executed (% d ms)", duration);
    lastActivityTime = millis();
  }

  void update() {
    uint32_t now = millis();

    if (_isArmed && _fState == FiringState::IDLE &&
        (now - _lastActivityTime > Config::AUTO_DISARM_MS)) {
      disarm();
    }

    switch (_fState) {
    case FiringState::IDLE:
      break;

    case FiringState::ESC_TEST:
      break; // Bleibt aktiv bis STOP kommt

    case FiringState::SPINNING_UP:
      if (now - _stateStartTime >= Config::SPINUP_MS) {
        _shot.attach(Config::PIN_SHOT);
        _shot.writeMicroseconds(shotNeutralUs + Config::SHOT_SPEED_OFFSET);
        _fState = FiringState::PUSHING;
        _stateStartTime = now;
      }
      break;

    case FiringState::ARMING:
      if (now - _stateStartTime >= Config::ARM_DELAY_MS) {
        _isArmed = true;
        _fState = FiringState::IDLE;
        debugPrint(F("OK: SYSTEM ARMED"));
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
        _escL.writeMicroseconds(Config::ESC_ARM);
        _escR.writeMicroseconds(Config::ESC_ARM);
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

    if (_tState == TiltState::MOVING && now >= _tiltEndTime) {
      _tilt.writeMicroseconds(tiltNeutralUs);
      delay(50);
      _tilt.detach();
      _tState = TiltState::IDLE;
      debugPrint(F("OK: TILT STOPPED"));
    }
  }

  void setZS(int v) {
    shotNeutralUs = v;
    debugPrintf("OK: Shot Zero set to %d", v);
  }

  void setD(int v) {
    shotDurationMs = v;
    debugPrintf("OK: Duration set to %d", v);
  }
};

class TiltController {
private:
  Servo _tilt;
  TiltState _state = TiltState::TILT_IDLE;
  uint32_t _endTime = 0;
  int _neutralUs;
  uint8_t _pin;

public:
  TiltController(uint8_t pin, int neutral) : _pin(pin), _neutralUs(neutral) {}

  void nudge(bool forward) {
    // Wir nutzen den vollen Pulsbereich für maximale Kompatibilität
    _shot.attach(Config::PIN_SHOT, 500, 2500);

    // Nutze deinen ermittelten Speed-Offset von 300 für genug Kraft
    int s = forward ? (shotNeutralUs + 300) : (shotNeutralUs - 300);

    _shot.writeMicroseconds(s);
    delay(100); // Von 40ms auf 100ms erhöht, damit der Motor Zeit zum Anlaufen
                // hat

    _shot.writeMicroseconds(shotNeutralUs);
    delay(50);
    _shot.detach();

    // Debug-Ausgabe zur Kontrolle im Monitor
    debugPrintf(forward ? "OK: Nudge Forward (Signal: %d)"
                        : "OK: Nudge Backward (Signal: %d)",
                s);
    _lastActivityTime = millis();
  }
  void move(bool up, uint32_t ms) {
    _tilt.attach(_pin);
    // Wir nutzen 2500/500 für max Speed, oder neutral +/- offset für sanftes
    // Bewegen
    _tilt.writeMicroseconds(up ? 2500 : 500);
    _endTime = millis() + ms;
    _state = TiltState::TILT_MOVING;
  }
  void startTilt(bool up, uint32_t ms) {
    _tilt.attach(Config::PIN_TILT);
    _tilt.writeMicroseconds(up ? 2500 : 500);
    _tiltEndTime = millis() + ms;
    _tState = TiltState::MOVING;
    debugPrintf("OK: Tilt move %d ms", (int)ms);
    recordActivity();
  }
  void update() {
    if (_state == TiltState::TILT_MOVING && millis() >= _endTime) {
      _tilt.writeMicroseconds(_neutralUs);
      delay(50); // Kurz Zeit zum Zentrieren geben
      _tilt.detach();
      _state = TiltState::TILT_IDLE;
    }
  }
  void setZT(int v) {
    tiltNeutralUs = v;
    debugPrintf("OK: Tilt Zero set to %d", v);
  }
  void setNeutral(int v) { _neutralUs = v; }
  int getNeutral() { return _neutralUs; }
};

// ###
class Comms {
  Launcher &_l;
  String _b;

public:
  Comms(Launcher &l) : _l(l) { _b.reserve(32); }
  void update() {
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') {
        if (_b.length() > 0)
          execute();
        _b = "";
      } else
        _b += c;
    }
  }
  void execute() {
    _b.trim();
    _b.toUpperCase();
    int spaceIdx = _b.indexOf(' ');
    String cmd = (spaceIdx == -1) ? _b : _b.substring(0, spaceIdx);
    int v = (spaceIdx == -1) ? 0 : _b.substring(spaceIdx + 1).toInt();

    if (cmd == "ARM")
      _l.arm();
    else if (cmd == "DISARM" || cmd == "STOP")
      _l.disarm();
    else if (cmd == "SHOT")
      _l.startFire(v > 0 ? v : 40);
    else if (cmd == "NF")
      _l.nudge(true);
    else if (cmd == "NB")
      _l.nudge(false);
    else if (cmd == "UP")
      _l.startTilt(true, v > 0 ? v : 200);
    else if (cmd == "DN")
      _l.startTilt(false, v > 0 ? v : 200);
    else if (cmd == "ZERO_S")
      _l.setZS(v);
    else if (cmd == "ZERO_T")
      _l.setZT(v);
    else if (cmd == "SET_SHOT")
      _l.setD(v);
    else if (cmd == "TEST_SHOT")
      _l.testShot(v);
    else if (cmd == "SAVE")
      _l.printConfig();
    else if (cmd == "HELP")
      _l.printHelp();
    else if (cmd == "STATUS")
      Serial.println(_l.isArmed() ? F("STATUS: ARMED") : F("STATUS: DISARMED"));
  }
};

Launcher nerf;
Comms comms(nerf);
Comms uartComms(nerfLauncher, Serial1);

void setup() {
  Serial.begin(Config::BAUD_RATE);
  Serial1.begin(Config::BAUD_RATE);
  while (!Serial)
    ;
  nerf.begin();
}

void loop() {
  nerf.update();
  comms.update();
  uartComms.update(); // Hardware UART Kanal
}