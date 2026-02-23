//
// Created by tozzi on 18.02.2026.
//

#include "TiltController.h"

TiltController::TiltController(uint8_t pin, int neutral) :
    _state(State::IDLE), _stateEndTime(0), _nudgeUp(true), _pin(pin), _neutralUs(neutral) {}

/**
 * @brief Updates servo state.
 *
 * Checks if the movement duration has elapsed. If so, stops sending
 * PWM signals (detach) to prevent heating/jitter at the proper position.
 */
void TiltController::update() {
    uint32_t now = millis();
    if (_state != State::IDLE && now >= _stateEndTime) {
        if (_state == State::MOVING) {
            _tiltServo.writeMicroseconds(_neutralUs);
            _stateEndTime = now + 50;  // Give time to center
            _state = State::CENTERING;
        } else if (_state == State::NUDGING_OUT) {
            _tiltServo.writeMicroseconds(_neutralUs);
            _stateEndTime = now + 40;
            _state = State::NUDGING_IN;
        } else if (_state == State::CENTERING || _state == State::NUDGING_IN) {
            _tiltServo.detach();
            _state = State::IDLE;
            SerialOutput::print(F("OK: TILT STOPPED"));
        }
    }
}

/**
 * @brief Initiates a timed movement.
 *
 * Attaches the servo, writes the target position (MIN or MAX),
 * and sets the timer for later detachment.
 */
void TiltController::move(bool up, uint32_t ms) {
    uint32_t safeMs = constrain(ms, 10UL, 5000UL);  // bounds check
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);

    int target = up ? Config::SV_MAX_US : Config::SV_MIN_US;
    _tiltServo.writeMicroseconds(target);
    _stateEndTime = millis() + safeMs;
    _state = State::MOVING;

    SerialOutput::print(up ? F("OK: Tilt UP") : F("OK: Tilt DOWN"));
    SerialOutput::printf(" Duration: %ld ms", (long)safeMs);
}

void TiltController::nudge(bool up) {
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    int s = up ? (_neutralUs + 400) : (_neutralUs - 400);
    _tiltServo.writeMicroseconds(s);
    _stateEndTime = millis() + 80;
    _state = State::NUDGING_OUT;
    _nudgeUp = up;
    SerialOutput::print(up ? F("OK: Tilt Nudge UP") : F("OK: Tilt Nudge DOWN"));
}

void TiltController::setNeutral(int v) {
    int safeV = constrain(v, Config::SV_MIN_US, Config::SV_MAX_US);
    _neutralUs = safeV;
    SerialOutput::printf("OK: Tilt Zero set to %ld", (long)safeV);
}

void TiltController::setPosition(int us) {
    if (us < (int)Config::SV_MIN_US) us = (int)Config::SV_MIN_US;
    if (us > (int)Config::SV_MAX_US) us = (int)Config::SV_MAX_US;

    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    _tiltServo.writeMicroseconds(us);

    // reset moving state so update() doesn't detach immediately
    _state = State::IDLE;

    SerialOutput::printf("OK: TILT SET %ld", (long)us);
}

int TiltController::getNeutral() {
    return _neutralUs;
}