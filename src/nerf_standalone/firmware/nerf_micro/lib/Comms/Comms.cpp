//
// Created by tozzi on 18.02.2026.
//

#include "Comms.h"

// #include "../Debug/ESCCalibration.h"
#include "Help.h"

/*
extern void runCalibrateMax();

extern void runCalibrateMin();

extern void runTestSequence();
*/

Comms::Comms(Launcher &launcher, TiltController &tiltController, Stream &serialStream) :
    _launcher(launcher), _tilt(tiltController), _stream(serialStream) {
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
 * @brief Prüft auf neue serielle Daten und verarbeitet vollständige Textzeilen.
 *
 * Liest ankommende Buchstaben einzeln aus dem seriellen Puffer.
 * Ein Befehl gilt als vollständig, wenn ein Zeilenumbruchzeichen (\n oder \r) erkannt wird.
 * Verhindert das Blockieren des gesamten Roboters, da immer nur kurz gelesen wird.
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
 * @brief Der zentrale Befehls-Verteiler (Dispatcher).
 *
 * Zerlegt die empfangene Textzeile nach dem Leerzeichen in den
 * eigentlichen BEFEHL (cmd) und seinen WERT (argStr/val) und ruft dann
 * die passenden Methoden im Launcher oder TiltController auf.
 *
 * Befehle z.B.:
 * - ARM/DISARM: Sicherheit/Scharfstellen
 * - SHOT <ms>: Dart abfeuern
 * - UP/DN <ms>: Neigung verstellen
 * - CAL: ESCs im FSM-Modus kalibrieren
 * - STATUS: Aktuellen Status ausgeben
 */
void Comms::execute(String line) {
    line.trim();
    if (line.length() == 0) return;

    // Schutz vor Endlos-Schleifen (Loopback Protection).
    // Verhindert, dass das System seine EIGENEN System-Ausgaben ("OK: ", "ERR: ")
    // wieder als Befehl interpretiert, falls Sende-(TX) und Empfangs-(RX) Pins
    // am Raspberry versehentlich kurzgeschlossen sind oder ein Echo geschickt wird.
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

    // --- Befehls-Zuweisung (Routing) ---
    // Ordnet die empfangenen Text-Befehle den echten C++ Funktionen der Controller zu

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
    //    else if (cmd == "CAL_MAX") {
    // #ifdef DEBUG_CALIBRATION
    //        ESCCalibration calibrator(_launcher.getLeftESC(), _launcher.getRightESC());
    //        calibrator.calibrateMax();
    // #else
    //        _stream.println(F("ERR: Calibration disabled (Define DEBUG_CALIBRATION to enable)"));
    // #endif
    //    } else if (cmd == "CAL_MIN") {
    // #ifdef DEBUG_CALIBRATION
    //        ESCCalibration calibrator(_launcher.getLeftESC(), _launcher.getRightESC());
    //        calibrator.calibrateMin();
    // #else
    //        _stream.println(F("ERR: Calibration disabled"));
    // #endif
    //    } else if (cmd == "CAL_TEST") {
    // #ifdef DEBUG_CALIBRATION
    //        ESCCalibration calibrator(_launcher.getLeftESC(), _launcher.getRightESC());
    //        calibrator.testSequence();
    // #else
    //        _stream.println(F("ERR: Calibration disabled"));
    // #endif
    //    }

    else if (cmd == "CAL_MAX" || cmd == "CAL_MIN" || cmd == "CAL_TEST") {
        broadcast(F("ERR: Obsolete commands. Use 'CAL' state via FSM instead."));
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
        Help::printConfig();

    else if (cmd == "ZERO_T")
        _tilt.setNeutral(val);
    else if (cmd == "T_POS")
        _tilt.setPosition(val);

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