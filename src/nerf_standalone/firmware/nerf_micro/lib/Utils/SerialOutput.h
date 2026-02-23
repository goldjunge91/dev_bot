//
// Serial Output Utility
// Zentrale Klasse für Debug-Ausgaben auf Serial + Serial1
//

#ifndef SERIALOUTPUT_H
#define SERIALOUTPUT_H

#include <Arduino.h>  // Basis-Header der Arduino-Bibliothek
#include <stdio.h>
#include <string.h>

/**
 * @class SerialOutput
 * @brief Hilfsklasse für die simple und synchrone Ausgabe auf mehreren seriellen Schnittstellen.
 *
 * Alle Print-Befehle werden sowohl auf den internen USB-Port (`Serial`) als auch auf
 * die physischen UART-Pins (`Serial1`) geschrieben, sodass Debugging via Kabel und
 * Steuerung per RasPi zeitgleich möglich sind.
 */
class SerialOutput {
public:
    /**
     * @brief Gibt einen Flash-String (PROGMEM) auf den seriellen Schnittstellen aus.
     * @param msg Der Text-String im Flash-Speicher (muss das F() Makro verwenden).
     */
    static void print(const __FlashStringHelper *msg);  // __FlashStringHelper aus der
                                                        // Arduino-Bibliothek (hilft, RAM zu sparen)
    /**
     * @brief Gibt einen formatierten String mit bis zu zwei Zahlen (long) aus.
     * @param format Das prinft-ähnliche Format (z.B. "Wert: %ld").
     * @param value1 Erste einzusetzende Zahl.
     * @param value2 Zweite einzusetzende Zahl (optional, Standard 0).
     */
    static void printf(const char *format, long value1, long value2 = 0);
    /**
     * @brief Gibt einen formatierten String mit einer Zeichenkette ein.
     * @param format Das prinft-ähnliche Format (z.B. "Status: %s").
     * @param strValue Der einzusetzende String.
     */
    static void printf(const char *format, const char *strValue);
};

#endif  // SERIALOUTPUT_H
