#ifndef TILT_H
#define TILT_H

#include "Config.h"
#include <Arduino.h>
#include <Servo.h>

// Helper for print (since we are outside Launcher)
// We use a simple macro or function
inline void tiltDebug(const char *msg) {
  Serial.println(msg);
  Serial1.println(msg);
}

class TiltController {
private:
  Servo _tiltServo;
  bool _isMoving = false;
  uint32_t _endTime = 0;
  uint8_t _pin;
  int _neutralUs;

public:
  TiltController(uint8_t pin, int neutral) : _pin(pin), _neutralUs(neutral) {}

  void update() {
    if (_isMoving && millis() >= _endTime) {
      _tiltServo.writeMicroseconds(_neutralUs);
      delay(50); // Give time to center
      _tiltServo.detach();
      _isMoving = false;
      tiltDebug("OK: TILT STOPPED");
    }
  }

  void move(bool up, uint32_t ms) {
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);

    // Config::SV_MAX_US (2500) = UP
    // Config::SV_MIN_US (500)  = DOWN
    int target = up ? Config::SV_MAX_US : Config::SV_MIN_US;

    _tiltServo.writeMicroseconds(target);
    _endTime = millis() + ms;
    _isMoving = true;

    char buf[64];
    sprintf(buf, "OK: Tilt %s %d ms", up ? "UP" : "DOWN", (int)ms);
    tiltDebug(buf);
  }

  // Tilt-Nudge für präzises Ausrichten
  void nudge(bool up) {
    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    int s = up ? (_neutralUs + 400) : (_neutralUs - 400);
    _tiltServo.writeMicroseconds(s);
    delay(80);
    _tiltServo.writeMicroseconds(_neutralUs);
    delay(40);
    _tiltServo.detach();
    tiltDebug(up ? "OK: Tilt Nudge UP" : "OK: Tilt Nudge DOWN");
  }

  void setNeutral(int v) {
    _neutralUs = v;
    char buf[64];
    sprintf(buf, "OK: Tilt Zero set to %d", v);
    tiltDebug(buf);
  }

  int getNeutral() { return _neutralUs; }

  void setPosition(int us) {
    // Constraint safety
    if (us < Config::SV_MIN_US)
      us = Config::SV_MIN_US;
    if (us > Config::SV_MAX_US)
      us = Config::SV_MAX_US;

    _tiltServo.attach(_pin, Config::SV_MIN_US, Config::SV_MAX_US);
    _tiltServo.writeMicroseconds(us);

    // reset moving state so update() doesn't detach immediately
    _isMoving = false;

    char buf[64];
    sprintf(buf, "OK: TILT SET %d", us);
    tiltDebug(buf);
  }
};

#endif // TILT_H
