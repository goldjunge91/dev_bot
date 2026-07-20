//
// Created by tozzi on 18.02.2026.
//

#include "Comms.h"

#include "../Utils/Help.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

// #include "../Debug/ESCCalibration.h"

// 'Stream' aus der Arduino-Bibliothek (Datenstrom, z.B. Serial)
Comms::Comms(Launcher& launcher, TiltController& tiltController, Stream& serialStream) :
    _launcher(launcher), _tilt(tiltController), _stream(serialStream) {}

namespace {
// Fallunabhaengiger Prefix-Vergleich (Loopback-Schutz), ohne eine Kopie des
// gesamten Strings anzulegen (Ersatz fuer String::toUpperCase()+startsWith()).
bool startsWithCI(const char* s, const char* prefix) {
    while (*prefix) {
        if (toupper((unsigned char)*s) != toupper((unsigned char)*prefix)) return false;
        ++s;
        ++prefix;
    }
    return true;
}
}  // namespace

// -------------------------------------------------------------------------
// Communication Handler
// -------------------------------------------------------------------------

/**
 * @brief Prüft auf neue serielle Daten und verarbeitet vollständige Textzeilen.
 *
 * Liest ankommende Buchstaben einzeln aus dem seriellen Puffer.
 * Ein Befehl gilt als vollständig, wenn ein Zeilenumbruchzeichen (\n oder \r) erkannt wird.
 * Verhindert das Blockieren des gesamten Roboters, da immer nur kurz gelesen wird.
 *
 * Der Puffer hat eine harte Obergrenze (kBufferSize): laeuft er ohne Zeilenumbruch voll
 * (Rauschen, falsche Baudrate, fehlendes Terminierungszeichen), wird die Zeile verworfen
 * statt unbegrenzt zu wachsen (frueher: Arduino String ohne Laengenlimit).
 */
void Comms::update() {
    while (_stream.available()) {
        char c = _stream.read();
        if (c == '\n' || c == '\r') {
            if (_bufLen > 0 && !_overflow) {
                _buffer[_bufLen] = '\0';
                execute(_buffer);
            }
            _bufLen = 0;
            _overflow = false;
        } else if (c >= 32 && c <= 126) {
            if (_overflow) continue;  // Rest der ueberlangen Zeile verwerfen
            if (_bufLen >= kBufferSize - 1) {
                _overflow = true;
                _bufLen = 0;
                _stream.println(F("ERR: Line too long, discarded"));
            } else {
                _buffer[_bufLen++] = c;
            }
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
void Comms::execute(char* line) {
    // Trim leading/trailing spaces in-place
    while (*line == ' ') ++line;
    if (*line == '\0') return;
    char* end = line + strlen(line);
    while (end > line && *(end - 1) == ' ') --end;
    *end = '\0';
    if (*line == '\0') return;

    // Schutz vor Endlos-Schleifen (Loopback Protection).
    // Verhindert, dass das System seine EIGENEN System-Ausgaben ("OK: ", "ERR: ")
    // wieder als Befehl interpretiert, falls Sende-(TX) und Empfangs-(RX) Pins
    // am Raspberry versehentlich kurzgeschlossen sind oder ein Echo geschickt wird.
    static const char* const kBlockedPrefixes[] = {
        ">", "ERR", "OK", "STATUS:", "NERF", "---", "SHOT ZERO", "TILT ZERO"};
    for (const char* prefix : kBlockedPrefixes) {
        if (startsWithCI(line, prefix)) return;
    }

    // Tokenize: am ersten Leerzeichen aufteilen
    char* argStr = strchr(line, ' ');
    if (argStr) {
        *argStr = '\0';
        ++argStr;
        while (*argStr == ' ') ++argStr;
    } else {
        argStr = line + strlen(line);  // leeres Argument
    }
    char* cmd = line;
    for (char* p = cmd; *p; ++p) *p = toupper((unsigned char)*p);
    int val = atoi(argStr);

    // --- Befehls-Zuweisung (Routing) ---
    // Ordnet die empfangenen Text-Befehle den echten C++ Funktionen der Controller zu

    if (strcmp(cmd, "ARM") == 0)
        _launcher.getFSM().triggerArming();
    else if (strcmp(cmd, "DISARM") == 0)
        _launcher.getFSM().triggerDisarming();
    else if (strcmp(cmd, "STOP") == 0)
        _launcher.getFSM().triggerDisarming();
    else if (strcmp(cmd, "BRAKE") == 0)
        _launcher.getFSM().triggerBraking();
    else if (strcmp(cmd, "SHOT") == 0)
        _launcher.getFSM().triggerFire(val > 0 ? val : 5);

    else if (strcmp(cmd, "TEST_ESC") == 0)
        _launcher.getFSM().triggerEscTest(val >= 0 ? val : 20);
    else if (strcmp(cmd, "PWM") == 0)
        _launcher.setRawPWM(val);
    else if (strcmp(cmd, "CAL") == 0)
        _launcher.getFSM().triggerCalibration();

    else if (strcmp(cmd, "NF") == 0)
        _launcher.nudge(true);
    else if (strcmp(cmd, "NB") == 0)
        _launcher.nudge(false);
    else if (strcmp(cmd, "TEST_SHOT") == 0)
        _launcher.testShot(val);
    else if (strcmp(cmd, "DANGEROUS_SHOT") == 0)
        _launcher.dangerousShot(val);
    else if (strcmp(cmd, "ZERO_S") == 0)
        _launcher.setZS(val);
    else if (strcmp(cmd, "SET_SHOT") == 0)
        _launcher.setD(val);

    else if (strcmp(cmd, "UP") == 0)
        _tilt.move(true, val > 0 ? val : 200);
    else if (strcmp(cmd, "DN") == 0)
        _tilt.move(false, val > 0 ? val : 200);
    else if (strcmp(cmd, "TU") == 0)
        _tilt.nudge(true);
    else if (strcmp(cmd, "TD") == 0)
        _tilt.nudge(false);

    else if (strcmp(cmd, "SAVE") == 0 || strcmp(cmd, "SAVE_OLD") == 0)
        Help::printConfig(
            _launcher.getShotZero(), _launcher.getFSM().getShotNeutral(), _launcher.getShotDur());

    else if (strcmp(cmd, "ZERO_T") == 0)
        _tilt.setNeutral(val);
    else if (strcmp(cmd, "T_POS") == 0)
        _tilt.setPosition(val);

    else if (strcmp(cmd, "STATUS") == 0) {
        _stream.println(_launcher.getFSM().isArmed() ? F("STATUS: ARMED") : F("STATUS: DISARMED"));
    } else if (strcmp(cmd, "HELP") == 0) {
        Help::printHelp();
    } else {
        // CAL_MAX / CAL_MIN / CAL_TEST faellt hier bewusst durch (obsolete Kurzbefehle entfernt).
        if (strlen(cmd) > 1) {
            _stream.print(F("ERR: Unknown "));
            _stream.println(cmd);
        }
    }
}
