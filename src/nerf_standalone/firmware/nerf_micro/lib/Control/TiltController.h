//
// Created by tozzi on 18.02.2026.
//

#ifndef TILT_H
#define TILT_H

#include "../../include/Config.h"
// #include "../Utils/SerialOutput.h"
#include "SerialOutput.h"
#include <Arduino.h>
#include <Servo.h>

/**
 * @brief Controls the tilt servo for the launcher.
 *
 * Handles moving the tilt servo to Up/Down positions, nudging,
 * and setting specific angles. Uses non-blocking logic to detach
 * the servo after movement to save power and prevent jitter.
 */
class TiltController {
private:
    Servo _tiltServo;
    bool _isMoving;
    uint32_t _endTime;
    uint8_t _pin;
    int _neutralUs;

public:
    /**
     * @brief Constructor
     * @param pin The GPIO pin for the servo.
     * @param neutral The neutral (center) pulse width in microseconds.
     */
    TiltController(uint8_t pin, int neutral);

    /**
     * @brief Polled in the main loop to handle timed detach.
     */
    void update();

    /**
     * @brief Moves the tilt mechanism up or down.
     *
     * @param up True for UP, False for DOWN.
     * @param ms Duration to apply power (determines travel distance).
     */
    void move(bool up, uint32_t ms);

    /**
     * @brief Small incremental movement (debugging/tuning).
     * @param up Direction.
     */
    void nudge(bool up);

    /**
     * @brief Sets the internal "Neutral" reference value.
     * @param v Pulse width in microseconds.
     */
    void setNeutral(int v);

    /**
     * @brief Moves to a specific absolute position.
     * @param us Pulse width in microseconds (approx 1000-2000).
     */
    void setPosition(int us);

    int getNeutral();
};

#endif // TILT_H