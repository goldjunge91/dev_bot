#include "Help.h"

#include "SerialOutput.h"

#include <Arduino.h>

void Help::printHelp() {
    SerialOutput::print(F("\n--- COMMAND LIST ---"));
    SerialOutput::print(F(" [ SYSTEM ]"));
    SerialOutput::print(F(" > ARM / STOP / STATUS   - Flywheel & Safety"));
    SerialOutput::print(F(" > SAVE                  - Show Current Config"));
    SerialOutput::print(F(" [ FIRING ]"));
    SerialOutput::print(F(" > SHOT <pwr>            - Fire (0-100)"));
    SerialOutput::print(F(" > TEST_ESC <pwr>        - Flywheels Only"));
    SerialOutput::print(F(" > PWM <us>              - Manual ESC Signal"));
    SerialOutput::print(F(" > CAL                   - Calibrate ESCs"));
    SerialOutput::print(F(" > CAL_MAX / CAL_MIN     - Send Max/Min Throttle Setup"));
    SerialOutput::print(F(" > CAL_TEST              - Run ESC Test Sequence"));
    SerialOutput::print(F(" > TEST_SHOT <ms>        - Pusher Cycle Only"));
    SerialOutput::print(F(" > NF / NB               - Nudge Pusher"));
    SerialOutput::print(F(" [ TILT ]"));
    SerialOutput::print(F(" > UP / DN <ms>          - Move Tilt"));
    SerialOutput::print(F(" > ZERO_S / ZERO_T       - Set Neutrals"));
    SerialOutput::print(F("--------------------\n"));
}
