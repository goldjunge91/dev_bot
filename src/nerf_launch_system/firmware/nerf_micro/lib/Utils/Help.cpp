#include "Help.h"

/**
 * Zeigt das Hauptmenü und alle gültigen Konsolenbefehle an.
 * Wird standardmäßig aufgerufen, wenn der Benutzer "HELP" oder ein ungültiges Kommando sendet.
 */
void Help::printHelp() {
    // F() Makro aus der Arduino-Bibliothek: Legt den Textstring in den Read-Only Flash-Speicher
    SerialOutput::print(F("\n--- COMMAND LIST ---"));
    SerialOutput::print(F(" [ SYSTEM ]"));
    SerialOutput::print(F(" > ARM / STOP / STATUS   - Flywheel & Safety"));
    SerialOutput::print(F(" > SAVE                  - Show Current Config"));
    SerialOutput::print(F(" [ FIRING ]"));
    SerialOutput::print(F(" > SHOT <pwr>            - Fire (0-100)"));
    SerialOutput::print(F(" > TEST_ESC <pwr>        - Flywheels Only"));
    SerialOutput::print(F(" > PWM <us>              - Manual ESC Signal"));
    SerialOutput::print(F(" > CAL                   - Calibrate ESCs"));
    //    SerialOutput::print(F(" > CAL_MAX / CAL_MIN     - Send Max/Min Throttle Setup"));
    //    SerialOutput::print(F(" > CAL_TEST              - Run ESC Test Sequence"));
    SerialOutput::print(F(" > TEST_SHOT <ms>        - Pusher Cycle Only"));
    SerialOutput::print(F(" > NF / NB               - Nudge Pusher"));
    SerialOutput::print(F(" [ TILT ]"));
    SerialOutput::print(F(" > UP / DN <ms>          - Move Tilt"));
    SerialOutput::print(F(" > ZERO_S / ZERO_T       - Set Neutrals"));
    SerialOutput::print(F("--------------------\n"));
}

/**
 * Fragt die aktuellen Variablen aus den Controllern ab (z.B. Servo-Neutralpositionen)
 * und gibt sie formatiert zusammen mit Hardware-Konstanten aus.
 */
void Help::printConfig(int shotZero, int tiltNeutral, int shotDur) {
    SerialOutput::print(F("\n--- CURRENT CONFIG ---"));
    SerialOutput::printf("Shot Zero:     %ld us", (long)shotZero);
    SerialOutput::printf("Tilt Zero:     %ld us", (long)tiltNeutral);
    SerialOutput::printf("Shot Duration: %ld ms", (long)shotDur);
    SerialOutput::print(F("----------------------\n"));
}

void Help::printStartup(int shotZero, int tiltNeutral, int shotDur) {
    SerialOutput::print(F("================================"));
    SerialOutput::print(F("      NERF OS PRO ONLINE        "));
    SerialOutput::print(F("================================"));
    SerialOutput::printf("Baudrate:      %ld", (long)Config::BAUD_RATE);
    printConfig(shotZero, tiltNeutral, shotDur);
    SerialOutput::print(F("Type 'HELP' for commands."));
    SerialOutput::print(F("================================"));
}
