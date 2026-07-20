// test/mock_launcher/Arduino.h
// Vollständiger Arduino-Mock für native_launcher Tests.
// Selbstständig — kein Dependency auf adrianaxente/arduino-mock.
// Stellt ArduinoMock mit GMock für delay() + millis() bereit.
#pragma once

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <gmock/gmock.h>

// ── Arduino-Typen ────────────────────────────────────────────
typedef uint8_t byte;
typedef uint8_t boolean;
typedef unsigned long time_t_arduino;

// ── Arduino-Makros ───────────────────────────────────────────
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define LED_BUILTIN 13
#define LSBFIRST 0
#define MSBFIRST 1

// F() Makro: gibt const char* zurück — __FlashStringHelper ist char
typedef char __FlashStringHelper;
#define F(x) (x)

// ── Utility-Funktionen ───────────────────────────────────────
inline long constrain(long val, long lo, long hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}
inline long map(long x, long in_min, long in_max, long out_min, long out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// ── Serial Stub ──────────────────────────────────────────────
class SerialStub {
public:
    void begin(unsigned long) {}
    void print(const char*) {}
    void print(int) {}
    void print(long) {}
    void print(unsigned long) {}
    void println(const char*) {}
    void println(int) {}
    void println(long) {}
    void println(unsigned long) {}
    void println() {}
    int available() {
        return 0;
    }
    int read() {
        return -1;
    }
    void flush() {}
};

extern SerialStub Serial;
extern SerialStub Serial1;

// ── ArduinoMock ──────────────────────────────────────────────
// Stellt GMock-Methoden für verifizierbare Hardware-Calls bereit.
class ArduinoMock {
private:
    uint32_t _millis = 0;

public:
    // millis-Kontrolle (nicht gemockt — direkte Kontrolle ist besser für Timer-Tests)
    void setMillisRaw(uint32_t ms) {
        _millis = ms;
    }
    void addMillisRaw(uint32_t ms) {
        _millis += ms;
    }
    uint32_t getMillis() const {
        return _millis;
    }

    // GMock-Methoden — verifizierbar via EXPECT_CALL
    MOCK_METHOD(void, delay, (unsigned long ms), ());
    MOCK_METHOD(void, pinMode, (uint8_t pin, uint8_t mode), ());
    MOCK_METHOD(void, digitalWrite, (uint8_t pin, uint8_t val), ());
    MOCK_METHOD(int, digitalRead, (uint8_t pin), ());
    MOCK_METHOD(void, analogWrite, (uint8_t pin, int val), ());
    MOCK_METHOD(int, analogRead, (uint8_t pin), ());
};

ArduinoMock* arduinoMockInstance();
ArduinoMock* arduinoMockInstanceNice();
void releaseArduinoMock();

// ── Freie Funktionen ─────────────────────────────────────────
// Delegieren an die Singleton-Instanz
inline uint32_t millis() {
    return arduinoMockInstance()->getMillis();
}
inline void delay(unsigned long ms) {
    arduinoMockInstance()->delay(ms);
}
inline void pinMode(uint8_t p, uint8_t m) {
    arduinoMockInstance()->pinMode(p, m);
}
inline void digitalWrite(uint8_t p, uint8_t v) {
    arduinoMockInstance()->digitalWrite(p, v);
}
inline int digitalRead(uint8_t p) {
    return arduinoMockInstance()->digitalRead(p);
}
inline void analogWrite(uint8_t p, int v) {
    arduinoMockInstance()->analogWrite(p, v);
}
inline int analogRead(uint8_t p) {
    return arduinoMockInstance()->analogRead(p);
}
