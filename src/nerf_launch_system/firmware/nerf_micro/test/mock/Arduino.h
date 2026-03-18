// Arduino.h Mock für Native GoogleTest
// Stellt die minimal nötigen Arduino-Typen und -Funktionen bereit,
// damit FiringFSM.h und Config.h auf dem Host-PC kompilieren.

#ifndef ARDUINO_H_MOCK
#define ARDUINO_H_MOCK

#include <cstdint>
#include <cstdio>
#include <cstring>

// --- Mock millis() ---
// Globale Variable, die im Test gesetzt wird um die Zeit zu steuern.
extern uint32_t _mock_millis_value;
inline uint32_t millis()
{
  return _mock_millis_value;
}

// Hilfsfunktionen für Tests
inline void setMillis(uint32_t val)
{
  _mock_millis_value = val;
}
inline void advanceMillis(uint32_t delta)
{
  _mock_millis_value += delta;
}

// --- FlashStringHelper Stub ---
class __FlashStringHelper;
#define F(x) (x)

// --- Stub Serial ---
class MockSerial {
public:
  void print(const char *) {}
  void print(int) {}
  void print(unsigned long) {}
  void println(const char *) {}
  void println(int) {}
  void println(unsigned long) {}
  void println() {}
  void println(const __FlashStringHelper *) {}
  void print(const __FlashStringHelper *) {}
};

extern MockSerial Serial;
extern MockSerial Serial1;

// --- Arduino-Makros und -Funktionen (Stubs) ---
#define LED_BUILTIN 13
#define INPUT 0
#define OUTPUT 1
#define HIGH 1
#define LOW 0

inline void pinMode(int, int) {}
inline void digitalWrite(int, int) {}
inline void delay(unsigned long) {}
inline long constrain(long val, long lo, long hi)
{
  if (val < lo) {return lo;}
  if (val > hi) {return hi;}
  return val;
}
inline long map(long x, long in_min, long in_max, long out_min, long out_max)
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

#endif  // ARDUINO_H_MOCK
