// test/mock_comms/Arduino.h
// Arduino-Mock fuer native_comms Tests.
// Basiert auf test/mock_launcher/Arduino.h, ersetzt aber den einfachen
// SerialStub durch eine fuetterbare Stream-Mock-Klasse, da Comms::execute()
// direkt auf den uebergebenen Stream schreibt (Fehlermeldungen/STATUS).
#pragma once

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <gmock/gmock.h>
#include <string>

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

// F() Makro: gibt const char* zurueck — __FlashStringHelper ist char.
// (Comms.h deklariert nach der broadcast()-Bereinigung keine ueberladenen
// Methoden mehr, die char* und __FlashStringHelper* unterscheiden muessten,
// daher ist diese Vereinfachung — wie in mock_launcher/Arduino.h — sicher.)
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

// ── Stream Mock ──────────────────────────────────────────────
// Fuetterbar via feed(), Ausgabe abrufbar via output().
class Stream {
public:
    void begin(unsigned long) {}

    void print(const char* s) {
        _out += s;
    }
    void println(const char* s) {
        _out += s;
        _out += '\n';
    }
    void println() {
        _out += '\n';
    }

    int available() {
        return _inPos < _in.size() ? 1 : 0;
    }
    int read() {
        return _inPos < _in.size() ? (unsigned char)_in[_inPos++] : -1;
    }

    // Test-Helfer
    void feed(const char* data) {
        _in += data;
    }
    const std::string& output() const {
        return _out;
    }
    void clearOutput() {
        _out.clear();
    }

private:
    std::string _in;
    size_t _inPos = 0;
    std::string _out;
};

extern Stream Serial;
extern Stream Serial1;

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
