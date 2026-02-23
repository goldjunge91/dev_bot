//
// Created by tozzi on 18.02.2026.
//

#include "Comms.h"

#include "../Debug/ESCCalibration.h"
#include "../Utils/Help.h"

// Declare global helpers from main.cpp
extern void printConfig();

/*
extern void runCalibrateMax();

extern void runCalibrateMin();

extern void runTestSequence();
*/

Comms::Comms(Launcher &l, TiltController &t, Stream &s) : _launcher(l), _tilt(t), _stream(s) {
    _buffer.reserve(32);
}

void Comms::broadcast(const char *msg) {
    _stream.println(msg);
    // Wenn diese Instanz Serial ist, sende auch an Serial1 (und umgekehrt)
    if (&_stream == &Serial)
        Serial1.println(msg);
    else
        Serial.println(msg);
}

void Comms::broadcast(const __FlashStringHelper *msg) {
    _stream.println(msg);
    if (&_stream == &Serial)
        Serial1.println(msg);
    else
        Serial.println(msg);
}

// -------------------------------------------------------------------------
// Communcation Handler
// -------------------------------------------------------------------------

/**
 * @brief Checks for new serial data and processes complete lines.
 *
 * Reads characters from the stream one by one. Warning: This blocks
 * slightly if many characters are available, but usually returns quickly.
 * Handles both \n and \r as line terminators.
 */
void Comms::update() {
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

/**
 * @brief Main Command Dispatcher
 *
 * Parses the command string (CMD VALUE) and calls the corresponding
 * methods in Launcher or TiltController.
 *
 * Commands:
 * - ARM/DISARM: Safety control
 * - SHOT <ms>: Fire a shot
 * - UP/DN <ms>: Tilt control
 * - CAL: Enter calibration mode
 * - STATUS: Report system state
 */
void Comms::execute(String line) {
    line.trim();
    if (line.length() == 0) return;

    // Loopback Protection
    // Prevent the system from interpreting its own log output as commands
    // if TX is shorted to RX or during echo.
    String check = line;
    check.toUpperCase();
    if (check.startsWith(">") || check.startsWith("ERR") || check.startsWith("OK") ||
        check.startsWith("STATUS:") || check.startsWith("NERF") || check.startsWith("---") ||
        check.startsWith("SHOT ZERO") || check.startsWith("TILT ZERO")) {
        return;
    }

    int spaceIdx = line.indexOf(' ');
    String cmd = (spaceIdx == -1) ? line : line.substring(0, spaceIdx);
    String argStr = (spaceIdx == -1) ? "" : line.substring(spaceIdx + 1);

    cmd.toUpperCase();
    int val = argStr.toInt();

    // --- Command Routing ---
    // Map command strings to controller actions

    if (cmd == "ARM")
        _launcher.getFSM().triggerArming();
    else if (cmd == "DISARM")
        _launcher.getFSM().triggerDisarming();
    else if (cmd == "STOP")
        _launcher.getFSM().triggerDisarming();
    else if (cmd == "SHOT")
        _launcher.getFSM().triggerFire(val > 0 ? val : 40);
    else if (cmd == "TEST_ESC")
        _launcher.getFSM().triggerEscTest(val >= 0 ? val : 20);

    else if (cmd == "PWM")
        _launcher.setRawPWM(val);
    else if (cmd == "CAL")
        _launcher.getFSM().triggerCalibration();

    // Calibration & Test shortcuts
    else if (cmd == "CAL_MAX") {
#ifdef DEBUG_CALIBRATION
        ESCCalibration calibrator(_launcher.getLeftESC(), _launcher.getRightESC());
        calibrator.calibrateMax();
#else
        _stream.println(F("ERR: Calibration disabled (Define DEBUG_CALIBRATION to enable)"));
#endif
    } else if (cmd == "CAL_MIN") {
#ifdef DEBUG_CALIBRATION
        ESCCalibration calibrator(_launcher.getLeftESC(), _launcher.getRightESC());
        calibrator.calibrateMin();
#else
        _stream.println(F("ERR: Calibration disabled"));
#endif
    } else if (cmd == "CAL_TEST") {
#ifdef DEBUG_CALIBRATION
        ESCCalibration calibrator(_launcher.getLeftESC(), _launcher.getRightESC());
        calibrator.testSequence();
#else
        _stream.println(F("ERR: Calibration disabled"));
#endif
    } else if (cmd == "NF")
        _launcher.nudge(true);
    else if (cmd == "NB")
        _launcher.nudge(false);
    else if (cmd == "TEST_SHOT")
        _launcher.testShot(val);
    else if (cmd == "ZERO_S")
        _launcher.setZS(val);
    else if (cmd == "SET_SHOT")
        _launcher.setD(val);

    else if (cmd == "UP")
        _tilt.move(true, val > 0 ? val : 200);
    else if (cmd == "DN")
        _tilt.move(false, val > 0 ? val : 200);
    else if (cmd == "TU")
        _tilt.nudge(true);
    else if (cmd == "TD")
        _tilt.nudge(false);

    else if (cmd == "SAVE" || cmd == "SAVE_OLD")
        ::printConfig();

    else if (cmd == "ZERO_T")
        _tilt.setNeutral(val);
    else if (cmd == "T_POS")
        _tilt.setPosition(val);

    /*
        else if (cmd == "STATUS") {
            _stream.println(_launcher.getFSM().isArmed()
                                ? F("STATUS: ARMED")
                                : F("STATUS: DISARMED"));
        } else {
            if (cmd.length() > 1) {
                _stream.print(F("ERR: Unknown "));
                _stream.println(cmd);
            }
        }
    */
    else if (cmd == "STATUS") {
        _stream.println(_launcher.getFSM().isArmed() ? F("STATUS: ARMED") : F("STATUS: DISARMED"));
    } else if (cmd == "HELP") {
        Help::printHelp();
    } else {
        if (cmd.length() > 1) {
            _stream.print(F("ERR: Unknown "));
            _stream.println(cmd);
        }
    }
}