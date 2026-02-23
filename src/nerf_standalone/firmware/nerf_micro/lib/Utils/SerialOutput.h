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
    static void print(const __FlashStringHelper *msg);
    static void printf(const char *format, long value1, long value2 = 0);
    static void printf(const char *format, const char *strValue);
};

#endif  // SERIALOUTPUT_H
