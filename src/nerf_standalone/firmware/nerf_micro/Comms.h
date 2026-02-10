#ifndef COMMS_H
#define COMMS_H

#include "Launcher.h"
#include "Tilt.h"
#include <Arduino.h>

class Comms {
private:
  Launcher &_launcher;
  TiltController &_tilt;
  Stream &_stream;
  String _buffer;

  // Helper for broadcasting to both Serial ports
  void broadcast(const char *msg) {
    _stream.println(msg);
    if (&_stream == &Serial)
      Serial1.println(msg);
    else
      Serial.println(msg);
  }
  void broadcast(const __FlashStringHelper *msg) {
    _stream.println(msg);
    if (&_stream == &Serial)
      Serial1.println(msg);
    else
      Serial.println(msg);
  }

  void printConfig() {
    broadcast(F("\n--- CURRENT CONFIG ---"));
    char buf[64];

    sprintf(buf, "Shot Zero:     %d us", _launcher.getShotZero());
    broadcast(buf);

    sprintf(buf, "Tilt Zero:     %d us", _tilt.getNeutral());
    broadcast(buf);

    sprintf(buf, "Shot Duration: %d ms", _launcher.getShotDur());
    broadcast(buf);

    broadcast(F("----------------------"));
  }

public:
  // Updated Constructor: Takes both Launcher and TiltController
  Comms(Launcher &l, TiltController &t, Stream &s)
      : _launcher(l), _tilt(t), _stream(s) {
    _buffer.reserve(32);
  }

  void update() {
    while (_stream.available()) {
      char c = _stream.read();
      if (c == '\n' || c == '\r') {
        if (_buffer.length() > 0) {
          execute(_buffer);
          _buffer = "";
        }
      } else if (c >= 32 && c <= 126) {
        _buffer += c;
      }
    }
  }

  void execute(String line) {
    line.trim();
    if (line.length() == 0)
      return;

    // Loopback Protection
    // Only ignore already-formatted firmware output (e.g. "OK:", "ERR:", "STATUS:")
    // Previously this ignored bare "STATUS" which prevented the STATUS command
    // from being processed. Match the colon-suffixed forms to avoid swallowing
    // incoming commands.
    String check = line;
    check.toUpperCase();
    if (check.startsWith(">") || check.startsWith("ERR") ||
        check.startsWith("OK") || check.startsWith("STATUS:") ||
        check.startsWith("NERF") || check.startsWith("---") ||
        check.startsWith("SHOT ZERO") || check.startsWith("TILT ZERO")) {
      return;
    }

    int spaceIdx = line.indexOf(' ');
    String cmd = (spaceIdx == -1) ? line : line.substring(0, spaceIdx);
    String argStr = (spaceIdx == -1) ? "" : line.substring(spaceIdx + 1);

    cmd.toUpperCase();
    int val = argStr.toInt();

    // Command Routing
    if (cmd == "ARM")
      _launcher.arm();
    else if (cmd == "DISARM")
      _launcher.disarm();
    else if (cmd == "STOP")
      _launcher.disarm();
    else if (cmd == "SHOT")
      _launcher.startFire(val > 0 ? val : 40);
    else if (cmd == "TEST_ESC")
      _launcher.testEsc(val > 0 ? val : 20);

    else if (cmd == "PWM")
      _launcher.setRawPWM(val);

    else if (cmd == "CAL")
      _launcher.startCalibration();

    // Manual Calibration (User Request)
    else if (cmd == "1")
      _launcher.calibrateMax();
    else if (cmd == "0")
      _launcher.calibrateMin();
    else if (cmd == "2")
      _launcher.testSequence();

    else if (cmd == "NF")
      _launcher.nudge(true);
    else if (cmd == "NB")
      _launcher.nudge(false);
    else if (cmd == "TEST_SHOT")
      _launcher.testShot(val);
    else if (cmd == "ZERO_S")
      _launcher.setZS(val);
    else if (cmd == "SET_SHOT")
      _launcher.setD(val);

    // Routed to TiltController
    else if (cmd == "UP")
      _tilt.move(true, val > 0 ? val : 200);
    else if (cmd == "DN")
      _tilt.move(false, val > 0 ? val : 200);
    else if (cmd == "TU")
      _tilt.nudge(true);
    else if (cmd == "TD")
      _tilt.nudge(false);
    else if (cmd == "SAVE") {
      printConfig();
    } else if (cmd == "SAVE_OLD") {
      printConfig(); // Unified behavior
    } else if (cmd == "ZERO_T")
      _tilt.setNeutral(val);
    else if (cmd == "T_POS")
      _stream.println(F("ERR: T_POS disabled. Use UP/DN <ms>."));
    else if (cmd == "HELP")
      _launcher.printHelp(); // Launcher handles help text
    else if (cmd == "STATUS") {
      _stream.println(_launcher.isArmed() ? F("STATUS: ARMED")
                                          : F("STATUS: DISARMED"));
    } else {
      if (cmd.length() > 1) {
        _stream.print(F("ERR: Unknown "));
        _stream.println(cmd);
      }
    }
  }
};

#endif // COMMS_H
