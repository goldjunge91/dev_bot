//
// Serial Output Utility
// Zentrale Klasse für Debug-Ausgaben auf Serial + Serial1
//

#include "SerialOutput.h"

// 1. Flash-String-Ausgabe (F() Makro) - spart RAM!
void SerialOutput::print(const __FlashStringHelper *msg) {
    Serial.println(msg);
    Serial1.println(msg);
}

// 2. Formatierte Ausgabe (Text + Zahl)
void SerialOutput::printf(const char *format, long value1, long value2) {
    char buf[64];
    snprintf(buf, sizeof(buf), format, value1, value2);
    Serial.println(buf);
    Serial1.println(buf);
}

// 3. Sichere String-Überladung für %s (Umgeht Casting-Probleme)
void SerialOutput::printf(const char *format, const char *strValue) {
    char buf[64];
    snprintf(buf, sizeof(buf), format, strValue);
    Serial.println(buf);
    Serial1.println(buf);
}
