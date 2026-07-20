#include "ESCCalibration.h"

#ifdef DEBUG_CALIBRATION

ESCCalibration::ESCCalibration(Servo &escL, Servo &escR) : _escLeft(escL), _escRight(escR) {}

/**
 * @brief Signals the ESCs to enter calibration mode (MAX throttle).
 *
 * Instructions:
 * 1. Disconnect battery.
 * 2. Send CAL (this method).
 * 3. Connect battery -> ESCs beep special tone.
 */
void ESCCalibration::calibrateMax() {
    if (!_escLeft.attached())
        _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    if (!_escRight.attached())
        _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_MAX);
    _escRight.writeMicroseconds(Config::ESC_MAX);
    SerialOutput::print(F("Sending maximum throttle"));
}

void ESCCalibration::calibrateMin() {
    if (!_escLeft.attached())
        _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    if (!_escRight.attached())
        _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_MIN);
    _escRight.writeMicroseconds(Config::ESC_MIN);
    SerialOutput::print(F("Sending minimum throttle"));
}

void ESCCalibration::testSequence() {
    SerialOutput::print(F("Running test in 3..."));
    delay(1000);
    SerialOutput::print(F("Running test in 2..."));
    delay(1000);
    SerialOutput::print(F("Running test in 1..."));
    delay(1000);

    for (uint16_t i = Config::ESC_MIN; i <= Config::ESC_MAX; i += 5) {
        _escLeft.writeMicroseconds(i);
        _escRight.writeMicroseconds(i);
        SerialOutput::printf("Pulse length = %ld", (long)i);
        delay(200);
    }
    SerialOutput::print(F("STOP"));
    _escLeft.writeMicroseconds(Config::ESC_MIN);
    _escRight.writeMicroseconds(Config::ESC_MIN);
}

#endif  // DEBUG_CALIBRATION
