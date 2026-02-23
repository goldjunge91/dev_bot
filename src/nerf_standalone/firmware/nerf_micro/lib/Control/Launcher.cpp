//
// Created by tozzi on 18.02.2026.
//

#include "Launcher.h"

// WICHTIG: Die statische Instanz initialisieren
Launcher *Launcher::_instance = nullptr;

Launcher::Launcher() :
    _fsm(callbackESCPower,
         callbackShotServo,
         callbackAttachESCs,
         callbackDetachESCs,
         callbackAttachShot,
         callbackDetachShot,
         callbackDebug) {
    _instance = this;  // Registered for static callbacks
}

void Launcher::begin() {
    if (_escLeft.attached()) _escLeft.detach();
    if (_escRight.attached()) _escRight.detach();
    _shot.detach();
}

void Launcher::update() {
    _fsm.evalTransition();
    _fsm.evalState();

    // === NEW NON-BLOCKING MANUAL LOGIC ===
    uint32_t now = millis();
    if (_manualState != ManualState::IDLE && now >= _manualTimer) {
        if (_manualState == ManualState::TEST_SHOT_PUSH) {
            _shot.writeMicroseconds(_fsm.getShotNeutral() - Config::BRAKE_OFFSET);
            _manualTimer = now + Config::BRAKE_MS;
            _manualState = ManualState::TEST_SHOT_BRAKE;
        } else if (_manualState == ManualState::TEST_SHOT_BRAKE) {
            _shot.writeMicroseconds(_fsm.getShotNeutral());
            _manualTimer = now + 50;
            _manualState = ManualState::TEST_SHOT_CENTER;
        } else if (_manualState == ManualState::TEST_SHOT_CENTER ||
                   _manualState == ManualState::NUDGE_CENTER) {
            _shot.detach();
            _manualState = ManualState::IDLE;
        } else if (_manualState == ManualState::NUDGE_OUT) {
            _shot.writeMicroseconds(_fsm.getShotNeutral());
            _manualTimer = now + 50;
            _manualState = ManualState::NUDGE_CENTER;
        }
    }
}

// --- HARDWARE IMPLEMENTATION ---

/**
 * @brief Setzt die ESC-Leistung durch Mapping von 0-100% auf die PWM-Signalbreite (us).
 */
void Launcher::setESCPower(int powerPercent) {
    int powerLimit = constrain(powerPercent, 0, 100);
    int us = map(powerLimit, 0, 100, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(us);
    _escRight.writeMicroseconds(us);
}

void Launcher::setShotServo(int us) {
    _shot.writeMicroseconds(us);
}

void Launcher::attachESCs() {
    _escLeft.attach(Config::PIN_ESC_LEFT, Config::ESC_MIN, Config::ESC_MAX);
    _escRight.attach(Config::PIN_ESC_RIGHT, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(Config::ESC_ARM);
    _escRight.writeMicroseconds(Config::ESC_ARM);
}

void Launcher::detachESCs() {
    if (_escLeft.attached()) _escLeft.detach();
    if (_escRight.attached()) _escRight.detach();
}

void Launcher::attachShotServo() {
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
}

void Launcher::detachShotServo() {
    _shot.detach();
}

// --- STATIC CALLBACK WRAPPERS ---
// These allow the FSM (which processes logic) to call hardware methods
// on the global/singleton Launcher instance.

void Launcher::callbackESCPower(int pwr) {
    _instance->setESCPower(pwr);
}
void Launcher::callbackShotServo(int us) {
    _instance->setShotServo(us);
}
void Launcher::callbackAttachESCs() {
    _instance->attachESCs();
}
void Launcher::callbackDetachESCs() {
    _instance->detachESCs();
}
void Launcher::callbackAttachShot() {
    _instance->attachShotServo();
}
void Launcher::callbackDetachShot() {
    _instance->detachShotServo();
}

void Launcher::callbackDebug(const char *msg) {
    // Workaround for RAM strings: use printf with %s
    SerialOutput::printf("%s", msg);
}

// --- HARDWARE ACTIONS (not FSM-controlled) ---

void Launcher::testShot(int ms) {
    int safeDur = constrain(ms, 10, 5000);  // bounds check
    int duration = (ms > 0) ? safeDur : _fsm.getShotDuration();
    SerialOutput::printf("OK: Test shot %ld ms", (long)duration);

    bool escWasAttached = _escLeft.attached() || _escRight.attached();
    if (_escLeft.attached() || _escRight.attached()) {
        detachESCs();
    }
    if (escWasAttached) {
        SerialOutput::print(F("WARN: ESCs were attached during TEST_SHOT; forced stop."));
    }

    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    _shot.writeMicroseconds(_fsm.getShotNeutral() + Config::TEST_SHOT_OFFSET);
    _manualTimer = millis() + duration;  // non-blocking sequence start
    _manualState = ManualState::TEST_SHOT_PUSH;
    _fsm.recordActivity();
}

// Methods calibrateMax, calibrateMin, testSequence removed (moved to
// ESCCalibration)

void Launcher::nudge(bool forward) {
    SerialOutput::print(F("STATUS: Nudging..."));
    _shot.attach(Config::PIN_SHOT, Config::SV_MIN_US, Config::SV_MAX_US);
    int s = forward ? (_fsm.getShotNeutral() + 500) : (_fsm.getShotNeutral() - 500);
    _shot.writeMicroseconds(s);

    _manualTimer = millis() + 200;  // non-blocking sequence start
    _manualState = ManualState::NUDGE_OUT;

    char buf[64];
    snprintf(buf, sizeof(buf), "OK: Nudge %s (Signal: %d)", forward ? "Fwd" : "Back", s);
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
    int safeUs = constrain(us, Config::ESC_MIN, Config::ESC_MAX);
    _escLeft.writeMicroseconds(safeUs);
    _escRight.writeMicroseconds(safeUs);
    SerialOutput::printf("OK: Manual PWM %ld us", (long)safeUs);
}

void Launcher::setZS(int v) {
    int safeV = constrain(v, Config::SV_MIN_US, Config::SV_MAX_US);
    _fsm.setShotNeutral(safeV);
    SerialOutput::printf("OK: Shot Zero set to %ld", (long)safeV);
}

void Launcher::setD(int v) {
    int safeV = constrain(v, 10, 5000);
    _fsm.setShotDuration(safeV);
    SerialOutput::printf("OK: Duration set to %ld", (long)safeV);
}