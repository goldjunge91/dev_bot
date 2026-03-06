#ifndef ESCCALIBRATION_H
#define ESCCALIBRATION_H

#ifdef DEBUG_CALIBRATION

#include "Config.h"
#include "SerialOutput.h"

#include <Arduino.h>
#include <Servo.h>

/**
 * @brief Helper class for ESC calibration and testing.
 *
 * Only active if DEBUG_CALIBRATION is defined.
 * Provides sequences to set ESC endpoints and test motor response.
 */
class ESCCalibration {
private:
    Servo &_escLeft;
    Servo &_escRight;

public:
    ESCCalibration(Servo &escL, Servo &escR);

    /**
     * @brief Sends Maximum Throttle (2000us).
     * Used as the first step in ESC calibration.
     */
    void calibrateMax();

    /**
     * @brief Sends Minimum Throttle (1000us).
     * Used to finalize ESC calibration.
     */
    void calibrateMin();

    /**
     * @brief Runs a ramp-up/ramp-down test sequence.
     * WARNING: Motors will spin!
     */
    void testSequence();
};

#endif  // DEBUG_CALIBRATION
#endif  // ESCCALIBRATION_H
