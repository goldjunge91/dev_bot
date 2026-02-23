//
// Serial Output Utility
// Zentrale Klasse für Debug-Ausgaben auf Serial + Serial1
//

#ifndef SERIALOUTPUT_H
#define SERIALOUTPUT_H

#include <Arduino.h>
#include <stdio.h>
#include <string.h>

class SerialOutput {
public:
  // 1. Flash-String-Ausgabe (F() Makro) - spart RAM!
  static void print(const __FlashStringHelper *msg) {
    Serial.println(msg);
    Serial1.println(msg);
  }

  // 2. Formatierte Ausgabe (Text + Zahl)
  static void printf(const char *format, long value1, long value2 = 0) {
    char buf[64];
    if (strstr(format, "%s")) {
      // Special case for %s to avoid compiler warnings about format type
      // mismatch This is a hack for the simplified printf
      sprintf(buf, format, (char *)value1, value2);
    } else {
      sprintf(buf, format, value1, value2);
    }
    Serial.println(buf);
    Serial1.println(buf);
  }
};

#endif // SERIALOUTPUT_H
