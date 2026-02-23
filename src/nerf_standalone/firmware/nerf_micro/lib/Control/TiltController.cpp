//
// Created by tozzi on 18.02.2026.
//

#include "TiltController.h"

TiltController::TiltController(uint8_t pin, int neutral) :
    _isMoving(false), _endTime(0), _pin(pin), _neutralUs(neutral) {}

/**
 * @brief Updates servo state.
 *
 * Checks if the movement duration has elapsed. If so, stops sending
 * PWM signals (detach) to prevent heating/jitter at the proper position.
 */
void TiltController::update() {
    if (_isMoving && millis() >= _endTime) {
        _tiltServo.writeMicroseconds(_neutralUs);
        delay(50);  // Give time to center
        _tiltServo.detach();
        _isMoving = false;
        SerialOutput::print(F("OK: TILT STOPPED"));
    }
}

/**
 * @brief Initiates a timed movement.
 *
 * Attaches the servo, writes the target position (MIN or MAX),
 * and sets the timer for later detachment.
 */
void TiltController::move(bool up, uint32_t ms) {
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);

    int target = up ? Config::SV_MAX_US : Config::SV_MIN_US;

    _tiltServo.writeMicroseconds(target);
    _endTime = millis() + ms;
    _isMoving = true;

    SerialOutput::print(up ? F("OK: Tilt UP") : F("OK: Tilt DOWN"));
    SerialOutput::printf(" Duration: %ld ms", (long)ms);
}

void TiltController::nudge(bool up) {
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    int s = up ? (_neutralUs + 400) : (_neutralUs - 400);
    _tiltServo.writeMicroseconds(s);
    delay(80);
    _tiltServo.writeMicroseconds(_neutralUs);
    delay(40);
    _tiltServo.detach();
    if (up)
        SerialOutput::print(F("OK: Tilt Nudge UP"));
    else
        SerialOutput::print(F("OK: Tilt Nudge DOWN"));
}

void TiltController::setNeutral(int v) {
    _neutralUs = v;
    //    char buf[64];
    //    sprintf(buf, "OK: Tilt Zero set to %d", v);
    //    SerialOutput::printf("%s", (long) buf);
    SerialOutput::printf("OK: Tilt Zero set to %ld", (long)v);
}

void TiltController::setPosition(int us) {
    if (us < (int)Config::SV_MIN_US) us = (int)Config::SV_MIN_US;
    if (us > (int)Config::SV_MAX_US) us = (int)Config::SV_MAX_US;

    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    _tiltServo.writeMicroseconds(us);

    // reset moving state so update() doesn't detach immediately
    _isMoving = false;

    //    char buf[64];
    //    sprintf(buf, "OK: TILT SET %d", us);
    //    SerialOutput::printf("%s", (long) buf);
    SerialOutput::printf("OK: TILT SET %ld", (long)us);
}

int TiltController::getNeutral() {
    return _neutralUs;
}