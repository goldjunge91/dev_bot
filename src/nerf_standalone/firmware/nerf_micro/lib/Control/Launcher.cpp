//
// Created by tozzi on 18.02.2026.
//

#include "Launcher.h"

// WICHTIG: Die statische Instanz initialisieren
Launcher *Launcher::_instance = nullptr;

Launcher::Launcher()
    : _fsm(callbackESCPower, callbackShotServo, callbackAttachESCs,
           callbackDetachESCs, callbackAttachShot, callbackDetachShot,
           callbackDebug) {
    _instance = this; // Registered for static callbacks
}

void Launcher::begin() {
    if (_escLeft.attached())
        _escLeft.detach();
    if (_escRight.attached())
        _escRight.detach();
    _shot.detach();
}

void Launcher::update() {
    _fsm.evalTransition();
    _fsm.evalState();
}

// --- HARDWARE IMPLEMENTATION ---

/**
 * @brief Sets ESC power via mapping 0-100% to PWM.
 */
void Launcher::setESCPower(int powerPercent) {
    int powerLimit = constrain(powerPercent, 0, 100);
    int us = map(powerLimit, 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(us);
    _escRight.writeMicroseconds(us);
}

void Launcher::setShotServo(int us) { _shot.writeMicroseconds(us); }

void Launcher::attachESCs() {
    _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_ARM);
    _escRight.writeMicroseconds(Config::ESC_ARM);
}

void Launcher::detachESCs() {
    if (_escLeft.attached())
        _escLeft.detach();
    if (_escRight.attached())
        _escRight.detach();
}

void Launcher::attachShotServo() {
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
}

void Launcher::detachShotServo() { _shot.detach(); }

// --- STATIC CALLBACK WRAPPERS ---
// These allow the FSM (which processes logic) to call hardware methods
// on the global/singleton Launcher instance.

void Launcher::callbackESCPower(int pwr) { _instance->setESCPower(pwr); }
void Launcher::callbackShotServo(int us) { _instance->setShotServo(us); }
void Launcher::callbackAttachESCs() { _instance->attachESCs(); }
void Launcher::callbackDetachESCs() { _instance->detachESCs(); }
void Launcher::callbackAttachShot() { _instance->attachShotServo(); }
void Launcher::callbackDetachShot() { _instance->detachShotServo(); }

void Launcher::callbackDebug(const char *msg) {
    // Workaround for RAM strings: use printf with %s
    SerialOutput::printf("%s", (long) msg);
}

// --- HARDWARE ACTIONS (not FSM-controlled) ---

void Launcher::testShot(int ms) {
    int duration = (ms > 0) ? ms : _fsm.getShotDuration();
    SerialOutput::printf("OK: Test shot %ld ms", (long) duration);

    bool escWasAttached = _escLeft.attached() || _escRight.attached();
    if (_escLeft.attached() || _escRight.attached()) {
        // Safety detach
        detachESCs();
    }
    if (escWasAttached) {
        SerialOutput::print(
            F("WARN: ESCs were attached during TEST_SHOT; forced stop."));
    }

    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    _shot.writeMicroseconds(_fsm.getShotNeutral() + Config::TEST_SHOT_OFFSET);
    delay(duration);

    _shot.writeMicroseconds(_fsm.getShotNeutral() - Config::BRAKE_OFFSET);
    delay(Config::BRAKE_MS);
    _shot.writeMicroseconds(_fsm.getShotNeutral());
    delay(50);
    _shot.detach();
    _fsm.recordActivity();
}

// Methods calibrateMax, calibrateMin, testSequence removed (moved to
// ESCCalibration)

void Launcher::nudge(bool forward) {
    SerialOutput::print(F("STATUS: Nudging..."));
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    int s =
            forward ? (_fsm.getShotNeutral() + 500) : (_fsm.getShotNeutral() - 500);
    _shot.writeMicroseconds(s);
    delay(200);
    _shot.writeMicroseconds(_fsm.getShotNeutral());
    delay(50);
    _shot.detach();

    char buf[64];
    sprintf(buf, "OK: Nudge %s (Signal: %d)", forward ? "Fwd" : "Back", s);
    Serial.println(buf);
    Serial1.println(buf);
    _fsm.recordActivity();
}

void Launcher::setRawPWM(int us) {
    if (!_fsm.isArmed()) {
        SerialOutput::print(F("ERR: Arm first!"));
        return;
    }
    if (!_escLeft.attached())
        _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    if (!_escRight.attached())
        _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);

    _escLeft.writeMicroseconds(us);
    _escRight.writeMicroseconds(us);
    SerialOutput::printf("OK: Manual PWM %d us", (long) us);
}

void Launcher::setZS(int v) {
    _fsm.setShotNeutral(v);
    SerialOutput::printf("OK: Shot Zero set to %d", v);
}

void Launcher::setD(int v) {
    _fsm.setShotDuration(v);
    SerialOutput::printf("OK: Duration set to %d", v);
}